# Italian Audio Overlay Assistant – Development Plan

## 1 — Main Goal
Build a desktop overlay that **listens to all audio (system + mic) in real‑time**, transcribes any Italian speech to text, live‑translates it into English, and instantly suggests an Italian reply—displayed in a translucent heads‑up UI. Latency target ≤ 1.5 s round‑trip while keeping API spend around **US $20 per month** at ~40 class‑hours.

---

## 2 — End‑to‑End Workflow
```mermaid
flowchart LR
    A[System & Mic Audio] --> B(Audio Capture)
    B --> C(STT ‑ Italian Text)
    C --> D(Translator ‑ English)
    D --> E(LLM Reply Generator)
    C -->|Italian transcript| UI
    D -->|English text| UI
    E -->|Suggested replies| UI
    UI[Overlay (React \| Electron)]
```

1. **Audio Capture** – Loop back system output and record mic.
2. **STT** – Stream audio to ASR engine; receive partial/ﬁnal Italian text.
3. **Translation** – Convert Italian → English.
4. **LLM Generator** – Produce 1–2 suitable Italian responses + English gloss.
5. **Overlay UI** – Render three live columns: *Italian*, *English*, *Reply*.

---

## 3 — Tech Stack & Key Tools
| Layer | Choice | Rationale |
|-------|--------|-----------|
| **Language/runtime** | Python 3.12 (back‑end) + TypeScript (React UI) | Great AI/ML ecosystem; easy inter‑process comms. |
| **Audio driver** | *VB‑Audio Cable* loopback (Win) or *BlackHole* (macOS) | Free, stable, ultra‑low latency. |
| **Audio I/O** | `sounddevice` (PortAudio/WASAPI) | Simple async streaming buffers. |
| **Speech‑to‑text** | **Primary:** Deepgram Nova‑3 streaming<br>**Fallback:** `faster‑whisper` (Whisper‑v3 int8, local GPU) | Deepgram ≈200 ms latency @ $0.012 / hr; local avoids network/outage risk. |
| **Translation** | DeepL API – “Pro” plan pay‑as‑you‑go | High quality, 50 ms average, ~$0.005 per 500 chars. |
| **LLM** | GPT‑4o mini (8k) streaming | $0.40 / M input tokens, $0.10 / M output; ~300 ms; best small‑budget quality. |
| **IPC** | `websockets` over `localhost` | Decouples Python pipeline from Electron front‑end. |
| **UI shell** | Electron w/ React + Tailwind | Fast dev, supports transparent always‑on‑top window. |
| **Packaging** | PyInstaller (back‑end), Electron Builder (front‑end) | Single‑click installer for Win/macOS. |
| **CI/CD** | GitHub Actions; unit tests via `pytest` | Auto‑build binaries on tag. |

---

## 4 — API‑Cost Budget (per 60 min lesson)
| Component | Tokens / Characters | Unit Price | Cost |
|-----------|--------------------|------------|------|
| Deepgram Nova‑3 | ~1 audio minute | $0.0002 | **$0.012** |
| DeepL | ~8 k chars | €0.00002 / char | **$0.01** |
| GPT‑4o mini | ~15 k tokens in/out | $0.0005 / token avg | **$7.50** |
| **Total (worst‑case)** | | | **≈ $7.52 / hr** |

> **Note:** Guided prompt engineering + caching (don’t re‑query LLM on pauses) typically cuts GPT cost by 70 %. Real‑world target ≈ $2 / hr. With a 10‑class month the $20 budget holds.

---

## 5 — Development Milestones
1. **Repo Setup**  
   * Create mono‑repo (`backend/`, `ui/`, `.github/workflows`).
2. **Audio Loopback Proof**  
   * Detect devices, stream to WAV ﬁle, verify sync. - current step
3. **Integrate STT**  
   * Async chunk (640 ms) → Deepgram websocket → print interim.
4. **Add Translation**  
   * Call DeepL REST, stream partial English text to console.
5. **Overlay MVP**  
   * Electron window, WebSocket client, display rolling transcripts.
6. **LLM Reply Suggestions**  
   * GPT‑4o mini streaming; keep 3‑minute context buffer.
7. **Latency Profiling & Caching**  
   * Time each stage, add local Phi‑3 as offline fallback.
8. **User Controls**  
   * Global hot‑key: toggle pipeline; push‑to‑speak muting.
9. **Installer & Release v0.1**  
   * Build Win/macOS packages; smoke‑test on clean VM.
10. **Telemetry & Logging**  
    * Optional Sentry + Prometheus exporter (CPU, GPU, dropped frames).

---

## 6 — Back‑End Skeleton (pseudo‑code)
```python
loop = asyncio.get_event_loop()

async def audio_source(queue):
    async for chunk in capture_stream():
        await queue.put(chunk)

async def stt_worker(in_q, out_q):
    async with deepgram_stream() as dg:
        while chunk := await in_q.get():
            dg.send(chunk)
            if text := dg.receive_partial():
                await out_q.put(text)

async def translate_worker(in_q, out_q):
    while it_text := await in_q.get():
        en_text = deepl_translate(it_text)
        await out_q.put((it_text, en_text))

async def lmm_worker(in_q, ws_clients):
    while it_text, en_text := await in_q.get():
        reply = gpt4o_suggest(en_text)
        payload = {"it": it_text, "en": en_text, "reply": reply}
        broadcast(ws_clients, payload)

# wire coroutines & run
```

---

## 7 — Key Risks & Mitigations
| Risk | Mitigation |
|------|------------|
| High GPT token cost | Cache identical prompts; suppress calls during silence; switch to Phi‑3 when quality drop acceptable. |
| Latency spikes on school Wi‑Fi | Pre‑emptively downsample audio; use jitter buffer; local fallback models. |
| OS audio driver updates | Keep signed installer for current VB‑Cable version; auto‑detect breakage on startup. |
| Privacy / FERPA concerns | Offer “local‑only” mode; encrypt logs; publish clear ToS. |

--- — Key Risks & Mitigations
| Risk | Mitigation |
|------|------------|
| High GPT token cost | Cache identical prompts; suppress calls during silence; switch to Phi‑3 when quality drop acceptable. |
| Latency spikes on school Wi‑Fi | Pre‑emptively downsample audio; use jitter buffer; local fallback models. |
| OS audio driver updates | Keep signed installer for current VB‑Cable version; auto‑detect breakage on startup. |
| Privacy / FERPA concerns | Offer “local‑only” mode; encrypt logs; publish clear ToS. |

---

*Last updated : 2025‑04‑29*

