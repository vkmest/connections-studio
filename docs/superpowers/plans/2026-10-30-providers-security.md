# Provider and credential security implementation plan

User requested local safe keys, setup instructions and free/local alternatives
while retaining OpenAI and adding other providers. Work in the existing branch.

1. Add fixed provider definitions: OpenAI, Moonshot/Kimi, DeepSeek, local Ollama.
   Provider-specific environment variables and credentials; never reuse a key
   across providers. No arbitrary remote URL or SDK environment URL override.
2. Add explicit OS-native keyring storage with no plaintext fallback. Store only
   provider/model preferences in user app data. Session-only remains default.
   Provide save/forget controls and CLI hidden-input credential commands.
3. Preserve OpenAI Responses; add validated chat JSON for Kimi/DeepSeek and native
   schema-constrained Ollama chat on 127.0.0.1. Reject cloud-backed local models,
   redirects and environment proxies. Unknown cloud rates remain unknown.
4. Add provider selector and credential isolation to Settings; update destination
   and local/free labels. Keep puzzle/feedback on provider change, reset service cache.
5. Test key isolation, sanitized errors, OS-store failure, no key persistence in
   preferences, cloud refusal, local image transport, malformed provider output,
   provider switching and CLI flags. Then run full suite, lint, build and review.
6. Document Windows key connection steps, realistic threat model, Ollama/Qwen
   installation commands and hardware tradeoffs. No automatic multi-GB downloads
   or paid calls; leave live verification limits explicit.

Current docs checked 2026-10-30: Kimi K2.5 API is retired; use kimi-k3.1-pro.
DeepSeek default is deepseek-flash (vision supported). Local Qwen3-VL 4B selected
as a practical starting point for this machine; accuracy is not benchmarked.

Completed: all six steps implemented. 62 offline tests pass, native Windows
credential round-trip verified with a disposable dummy entry, UI rendered and
inspected, lint/format/build checked. Independent review's two recovery findings
were reproduced and fixed. No paid calls or model downloads performed.
