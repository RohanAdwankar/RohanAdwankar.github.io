# semfont chat

The chat page behind the streaming example in the semfont post. It is not
published anywhere. The post's own box streams a canned reply in the browser;
this is the same page as a real app, with a route and a stand-in model, so the
snippets in the post have a working program behind them and a GIF of it can be
recorded for places where nothing runs.

Vite, React, the [AI SDK](https://ai-sdk.dev) for the stream, `SemanticText`
around each reply, and any model behind the OpenAI chat completions API.
OpenRouter by default.

```bash
npm install
OPENROUTER_API_KEY=sk-or-... npm run dev      # http://localhost:5173
```

`LLM_MODEL` picks the model, default `openai/gpt-oss-120b`. `LLM_BASE_URL`
points the provider somewhere else, including the mock below.

## Without a key

`mock/server.mjs` is a model stand-in that speaks the same API, streaming
included, so the app runs through the same provider code and cannot tell the
difference.

```bash
npm run mock                                   # :8787
LLM_BASE_URL=http://localhost:8787/v1 npm run dev
```

## Files

- `api/chat.mjs` streams one model call back in the AI SDK's UI message
  protocol. In production this is one route handler in whatever you deploy on.
- `src/App.jsx` is `useChat` plus `SemanticText` around the text of each
  assistant message. Every chunk re-runs the engine on the message so far.
  The page renders each reply twice, plain and set, so the difference is the
  only thing on screen. A real app renders the right-hand column alone.
- `mock/server.mjs` is the stand-in model. `MOCK_DELAY_MS` sets its cadence.
- `record/record.mjs` drives the page in Chromium and captures frames;
  `record/gif.py` assembles them into `record/semfont-stream.gif`.

## Re-recording

```bash
MOCK_DELAY_MS=120 npm run mock
LLM_BASE_URL=http://localhost:8787/v1 npm run dev
npx playwright install chromium               # once
npm run record
uv run --with pillow python record/gif.py
```
