# Active Context

## Current Work Focus

**Milestone 3 - Integrate STT**: Connect the audio stream from `backend/audio.py` to the Deepgram Nova-3 streaming Speech-to-Text service via WebSockets. Display interim and final transcription results.

## Recent Changes

1. **UI Mock Integration** (progress.md #1)
   - Created initial Electron/React UI, wired to `mockData.ts`.
   - Updated chat feed to render newest messages at the top.

2. **Monorepo & Backend Setup** (progress.md #2)
   - Initialized `backend/` directory with Python WebSocket server scaffold.
   - Added WebSocket client utility in the frontend, updated `package.json` and `scripts`.
   - Defined Python dependencies in `requirements.txt`.

3. **Windows Audio Capture** (progress.md #3)
   - Implemented and verified dual audio stream capture (loopback + mic) using `sounddevice` and WASAPI.
   - Resolved issues with device discovery and asyncio/callback threading.

4. **Deepgram STT Setup & Test** (progress.md #4, #7)
   - Created `backend/stt.py` with `DeepgramSTT` class for WebSocket management.
   - Added Deepgram SDK to `requirements.txt`.
   - Configured connection options and basic handlers.
   - Tracked connection state (`_is_connected`).
   - Resolved SDK event handler signature mismatches using `*args, **kwargs` and extracting data via `kwargs.get('key')`.
   - Successfully tested `stt.py` directly, confirming connection and event handling work without `TypeError`.

5. **Backend Integration (Audio -> STT)** (progress.md #5)
   - Successfully ran `main.py`, capturing system audio via loopback, sending to Deepgram, and receiving/logging transcripts (initially English due to config).

6. **Backend WebSocket Server for UI** (progress.md #6)
   - Configured for Italian & added WebSocket server (`ws://localhost:8765`) into `main.py`.
   - Modified `process_stt_output` to broadcast transcripts to connected clients.

7. **Frontend Integration (STT Display)** (progress.md #8)
   - Connected React UI (`App.tsx`) to backend WebSocket (`ws://localhost:8765`) via `src/utils/websocket.ts`.
   - Implemented message handler (`handleNewTranscript`) to update UI state.
   - Resolved CORS and React Strict Mode connection issues (using `setTimeout` workaround - see Tech Debt).
   - Successfully displayed live Italian transcripts from Deepgram in the UI overlay.

8. **Translation Integration (DeepL)** (progress.md #9)
   - Added `deepl` library and API key handling (`backend/translation.py`).
   - Integrated `translate_text` into backend pipeline (`main.py`).
   - Updated frontend state management (`App.tsx`) and UI (`TranscriptItem.tsx`) for English text.
   - Successfully displayed live Italian-to-English translations in the UI overlay.

9. **LLM Suggestion Integration (OpenAI)** (progress.md #10 - completed)
   - Integrated OpenAI client (`llm.py`).
   - Added suggestions to `main.py` pipeline.
   - Updated UI to display suggestions.

10. **Single Script Runner & Setup**
    - Created `run-app.bat`, `run-app.sh` and `scripts/setup.js`.
    - Refactored `package.json` to use system Python (removed venv dependency for runner).
    - Fixed Electron startup issues (`electron-is-dev` replacement).

11. **Multilingual Support & Renaming**
    - Configured Deepgram for `nova-3` multilingual model.
    - Updated DeepL to auto-detect source language.
    - Made UI components and types language-agnostic (using "Original" instead of "Italian").
    - Updated project name and README.

12. **User Settings & Contextual LLM**
    - Added Settings modal in UI (React component).
    - Implemented state management for settings (context, personal info, response language) in `App.tsx` using `localStorage`.
    - Backend (`main.py`) now receives and stores settings via WebSocket.
    - LLM prompt (`llm.py`) updated to use user settings and detected language for contextual replies.
    - UI layout fixes for settings modal and transcript items.

13. **Backend Processing Toggle**
    - Added UI toggle button (Power icon) in `OverlayWindow.tsx` with loading state.
    - Managed toggle state in `App.tsx`, sending `start/stop_processing` commands via WebSocket.
    - Backend (`main.py`) handles start/stop commands, manages `DeepgramSTT` client lifecycle (`start`/`stop`), clears audio queue on stop, and broadcasts `backend_status`.
    - Fixed duplicate transcription bug by moving `_register_handlers` in `stt.py` to `__init__`.
    - Refined LLM prompt (`llm.py`) to explicitly generate *answers* to questions, not repeat them.

## Next Steps

- **Implement Conversational Context for LLM:**
  - Store recent conversation history (e.g., last N turns) in `backend/main.py`.
  - Pass history to `get_llm_suggestions` in `llm.py`.
  - Update LLM system prompt to utilize conversation history.
- **Implement Selective LLM Answering:**
  - Modify LLM system prompt (`llm.py`) to instruct the AI to only generate suggestions when appropriate (e.g., for questions directed at the user) and return an empty list otherwise.
- **(Future)** Add Microphone Audio Processing: Modify `main.py` to also process/send microphone audio if needed.
- **(Future)** Refine Frontend WebSocket Connection: Address the `setTimeout` workaround for React Strict Mode in `App.tsx`.

## Active Decisions & Considerations

- **LLM Context Strategy:** How much history to send? Start with last N turns (e.g., 5-10), potentially add summarization later if needed to balance cost/context length.
- **LLM Selective Answering Reliability:** How reliable will prompt-based selective answering be? May need backend pre-filtering logic later if prompting alone is insufficient.
- **Speaker Identification:** Currently assuming all STT input is from the "other" speaker as microphone input is not yet processed.

## Important Patterns & Preferences

- **Async pipeline** in Python 3.12 using `asyncio` Queues and coroutines.
- **Test‑driven approach**: pytest for unit/integration, SOX‑based audio regression tests.
- **IPC over WebSockets**: decouples backend capture/processing from Electron/React overlay.
- **Device discovery** by substring match in `sounddevice.query_devices()` for cross‑platform flexibility.
- **Settings persistence** via `localStorage`.
- **Modular backend components** (`audio.py`, `stt.py`, `translation.py`, `llm.py`).

## Learnings & Project Insights

- Explicit device naming is crucial for reliable audio capture on Windows.
- Careful handling of asyncio event loops is required when interfacing with threaded libraries like `sounddevice`.
- **WASAPI** is the preferred host API for low-latency audio on Windows.
- **Blocksize tuning** is critical: 20 ms chunks strike the best balance between latency and throughput.
- **Device identification** will rely on matching device names like 'CABLE Output (VB-Audio Virtual Cable)' via `sounddevice.query_devices()`.
- **Deepgram SDK Handlers (`asyncwebsocket`)**: Calls handlers with the SDK client instance as the first positional argument and event data in `kwargs` (e.g., `kwargs['result']`, `kwargs['error']`). Use `*args, **kwargs` signature and `kwargs.get('key')` for robust handling.
- **Event handlers should typically be registered once during initialization, not repeatedly during start/stop cycles**.
- **Clear state management and status feedback** (e.g., `backend_status`) are crucial for reliable UI controls interacting with backend processes.
- **Explicit LLM prompting** is needed to guide behavior like *answering* vs. *repeating* questions.

## Technical Debt / Workarounds

- **Frontend WebSocket Connection (React Strict Mode):** The current WebSocket connection logic in `App.tsx` uses a `setTimeout` delay (100ms) within `useEffect` as a workaround for React Strict Mode's double invocation causing connection failures during development. This should be revisited to find a more robust solution that doesn't rely on timing, possibly by managing the WebSocket connection outside the component or using a dedicated library.

