"""An original, deterministic example. No API calls or publisher puzzle data."""

from connections.models import Group, Solution

DEMO_WORDS = [
    "BASS",
    "MERCURY",
    "ROSE",
    "HEARTS",
    "MARS",
    "CLUBS",
    "DRUMS",
    "LILY",
    "DIAMONDS",
    "TULIP",
    "VENUS",
    "GUITAR",
    "DAISY",
    "PIANO",
    "SPADES",
    "SATURN",
]


def demo_solution() -> Solution:
    categories = [
        (
            "In the flower garden",
            ["ROSE", "LILY", "TULIP", "DAISY"],
            "Four familiar flowering plants. Each one belongs in a bouquet.",
        ),
        (
            "Suits in a deck",
            ["HEARTS", "CLUBS", "DIAMONDS", "SPADES"],
            "The four suits found in a standard deck of playing cards.",
        ),
        (
            "Members of the band",
            ["BASS", "DRUMS", "GUITAR", "PIANO"],
            "Musical instruments you might hear playing together.",
        ),
        (
            "Our planetary neighbors",
            ["MERCURY", "MARS", "VENUS", "SATURN"],
            "Planets in our solar system, also named after Roman deities.",
        ),
    ]
    return Solution(
        groups=[
            Group(title=title, words=words, explanation=explanation, confidence="high")
            for title, words, explanation in categories
        ]
    )
