# Product Context

## Why This Project Exists

Language learners often struggle to follow fast-paced, authentic Italian audio—whether in lectures, conversations, or media—because they must juggle listening, comprehension, and formulating replies. Traditional flashcards or delayed subtitles don’t address the immediate gap when real-time interaction is needed.

This project provides an always-on, context-aware overlay that:

- **Captures live system and microphone audio** in real time.
- **Instantly transcribes** spoken Italian into text.
- **Translates** it to English on-the-fly.
- **Suggests** appropriate Italian responses.

By embedding translation and pedagogy directly into the user’s workflow, it transforms passive listening into active practice. (See `projectbrief.md` for detailed user stories and acceptance criteria.)

## How It Should Work

1. **Launch & Configuration**  
   - User installs the app (Windows/macOS) and selects audio devices once.  
   - App auto-detects environment (Linux dev vs. Windows production) via device name matching.

2. **Audio Capture**  
   - Virtual loopback driver (VB‑Audio Cable / BlackHole) clones system output; microphone is captured in parallel.
   - Python backend uses `sounddevice` to asynchronously read 20 ms chunks from both sources.

3. **Processing Pipeline**  
   - **STT Engine** (Deepgram streaming or local Whisper) transcribes Italian speech to text with <200 ms interim results.  
   - **Translation** (DeepL API) converts Italian text to English in ~50 ms.  
   - **Reply Generator** (GPT‑4o mini) uses the English gist + context buffer to suggest 1–2 Italian responses with an English gloss in ~300 ms.

4. **Overlay UI**  
   - Electron + React window set to always-on-top and transparent.  
   - Displays three columns:
     1. **Italian Transcript** (live-updating)  
     2. **English Translation** (live-updating)  
     3. **Reply Suggestions** (click-to-copy)  
   - Supports hot-keys to toggle visibility and muting.

5. **Continuous Operation**  
   - Maintains a rolling 3 min context buffer for more coherent suggestions.  
   - Caches repeated translations and prompts to reduce API costs.  
   - Logs performance metrics (latency, drift) for telemetry.

## User Experience Goals

| Goal              | Metric / Target                              |
|-------------------|-----------------------------------------------|
| **Real-time feel**| Round-trip latency ≤ 1.5 s for full loop.     |
| **Clarity**       | Text displays with legible fonts, dark mode. |
| **Non-intrusive** | Semi-transparent overlay; single hot-key toggle. |
| **Reliability**   | <1% audio-drop errors; auto-reconnect on failure. |
| **Affordability** | ≤ US $20 monthly API cost (Deepgram + DeepL + GPT). |

These principles ensure learners stay focused on conversation, not on tool mechanics.

