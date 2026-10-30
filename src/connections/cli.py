"""Terminal interface. Desktop dependencies are imported only when launching the UI."""

import argparse
import json
import re
import sys
from pathlib import Path

from connections.config import Settings
from connections.demo import demo_solution
from connections.images import clipboard_image, read_image
from connections.models import SolveRequest, Usage
from connections.service import ServiceError, SolverService


def parse_word_text(text: str) -> list[str]:
    """Newlines, tabs, commas and semicolons separate tiles; spaces belong to phrases."""
    return [word.strip() for word in re.split(r"[,;\n\r\t]+", text) if word.strip()]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="connections", description="Connections Studio")
    parser.add_argument("--version", action="version", version="Connections Studio 1.0.0")
    commands = parser.add_subparsers(dest="command")
    gui = commands.add_parser("gui", help="Open the desktop app (default)")
    gui.add_argument("--demo", action="store_true", help="Load a free offline example")
    for name in ("solve", "extract"):
        command = commands.add_parser(
            name,
            help="Solve a puzzle"
            if name == "solve"
            else "Read image words for review before solving",
        )
        source = command.add_mutually_exclusive_group(required=True)
        source.add_argument(
            "--image", type=Path, help="Path to a screenshot (quote paths with spaces)"
        )
        source.add_argument("--clipboard", action="store_true", help="Read a copied screenshot")
        if name == "solve":
            source.add_argument(
                "--words", help="16 entries separated by commas; keep phrases intact"
            )
            source.add_argument(
                "--words-file", type=Path, help="UTF-8 text file, one word per line"
            )
            source.add_argument("--demo", action="store_true", help="Offline example; no API usage")
            command.add_argument("--mode", choices=["budget", "deeper"], default="budget")
        command.add_argument("--json", action="store_true", help="Machine-readable output")
        command.add_argument("--model", help="Override CONNECTIONS_MODEL (advanced)")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command in (None, "gui"):
        try:
            from connections.gui.app import main as gui_main
        except ImportError:
            print('Desktop support is missing. Run: pip install -e ".[desktop]"', file=sys.stderr)
            return 1
        return gui_main(demo=getattr(args, "demo", False))
    service = None
    try:
        usage_records = []
        if getattr(args, "demo", False):
            solution = demo_solution()
        else:
            settings = Settings.from_environment()
            if args.model:
                settings = Settings(api_key=settings.api_key, model=args.model)
            service = SolverService(settings)
            if args.image or args.clipboard:
                image = read_image(args.image) if args.image else clipboard_image()
                extracted = service.extract(image)
                usage_records.append(extracted.usage)
                words = extracted.value.words
                if args.command == "extract":
                    if args.json:
                        print(
                            json.dumps(
                                {
                                    "extraction": extracted.value.model_dump(),
                                    "usage": extracted.usage.model_dump(),
                                },
                                indent=2,
                            )
                        )
                    else:
                        print("\n".join(words))
                        if extracted.value.warning:
                            print("Warning: " + extracted.value.warning, file=sys.stderr)
                    return 0
                if extracted.value.warning:
                    print("Warning: " + extracted.value.warning, file=sys.stderr)
            else:
                text = (
                    args.words_file.read_text(encoding="utf-8-sig")
                    if args.words_file
                    else args.words
                )
                words = parse_word_text(text)
            request = SolveRequest(words=words, mode=args.mode)
            result = service.solve(request)
            usage_records.append(result.usage)
            solution = result.value
        total = sum_usage(usage_records)
        if args.json:
            print(
                json.dumps(
                    {
                        "solution": solution.model_dump(),
                        "usage": total.model_dump(),
                        "demo": bool(args.demo),
                    },
                    indent=2,
                )
            )
        else:
            print("CONNECTIONS STUDIO" + (" / OFFLINE DEMO" if args.demo else ""))
            for index, group in enumerate(solution.groups, 1):
                print(f"\n{index}. {group.title} [{group.confidence} confidence]")
                print("   " + " / ".join(group.words))
                print("   " + group.explanation)
            cost = total.estimated_cost_usd
            print(
                f"\nEstimated API cost: ${cost:.5f}"
                if cost is not None
                else "\nAPI cost estimate unavailable for this model."
            )
            print("AI suggestions can be wrong. Confidence is not a measured probability.")
        return 0
    except (ServiceError, ValueError, OSError) as error:
        print("Error: " + str(error), file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("Cancelled. Any request already sent may still be billed.", file=sys.stderr)
        return 130
    finally:
        if service is not None:
            service.close()


def sum_usage(records: list[Usage]) -> Usage:
    return Usage(
        input_tokens=sum(record.input_tokens for record in records),
        output_tokens=sum(record.output_tokens for record in records),
        cached_input_tokens=sum(record.cached_input_tokens for record in records),
        estimated_cost_usd=(
            sum(record.estimated_cost_usd for record in records)
            if all(record.estimated_cost_usd is not None for record in records)
            else None
        ),
    )
