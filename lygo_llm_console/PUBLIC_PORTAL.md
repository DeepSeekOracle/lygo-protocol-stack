# Public LYGO LLM Portal

Live page: **https://chatagent.ca/portal/**

Same studio chrome as the public console. Inference is **not** your admin tree.

## Three ways to talk

| Mode | Who pays compute | Limbs |
|------|------------------|--------|
| **LYGO hosted** | Stream PC `public_gateway.py` behind HTTPS (set `web_portal/portal.json` `hosted_base`) | Chat + P0 + rate limit. No disks, no shell. |
| **Hugging Face** | Visitor’s HF account. Token stays in **their browser**. Default model `Qwen/Qwen2.5-1.5B-Instruct` via `router.huggingface.co` | Chat only. |
| **My local console** | Visitor’s PC at `http://127.0.0.1:9641` | Opt-in **Full LYGO limbs**. HTTPS sites often cannot fetch localhost (mixed content) — they should open the local BAT window. |
| **Custom URL** | Visitor’s OpenAI-compatible HTTPS (Space, tunnel, llama-server) | Chat. Full limbs only if that server is *their* console. |

## Stream PC (always-on)

Do **not** bind the admin console (`:9641`) to the internet.

```bat
python -u src\public_gateway.py --backend ollama --model qwen2.5:3b --lan --i-consent --port 9642
```

Caddy (example):

```
handle_path /llm/* {
  reverse_proxy 127.0.0.1:9642
}
```

Then set `hosted_base` to `https://YOUR.PUBLIC.HOST/llm`.

## Hugging Face Space (static mirror)

`data/hf-space-lygo-portal/` is a static Space: same HTML. Visitors still pick HF token or a custom HTTPS backend. Do not put steward tokens in the Space.

## Security contract

- Public gateway: CORS allowlist of LYGO domains, 24 req / 10 min / IP, P0 on in/out, no tools, no `admin.json`.
- Notepad on the public page = `localStorage` only.
- Full LYGO = local kit. Hub never replace CANON. Live Star Chart writes still need a human.
