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

4. **Deepgram STT Setup & Test**
   - Created `backend/stt.py` with `DeepgramSTT` class for WebSocket management.
   - Added Deepgram SDK to `requirements.txt`.
   - Configured connection options and basic handlers.
   - Tracked connection state (`_is_connected`).
   - Resolved SDK event handler signature mismatches using `*args, **kwargs` and extracting data via `kwargs.get('key')`.
   - Successfully tested `stt.py` directly, confirming connection and event handling work without `TypeError`.

5.4 - Successfully ran `main.py`, capturing system audio via loopback, sending to Deepgram, and receiving/logging transcripts (initially English due to config).

6) **Configure for Italian & Add WebSocket Server**
   - Updated Deepgram `LiveOptions` in `stt.py` to `language="it"`, `model="nova-2"`, `smart_format=True`.
   - Added `websockets` library to `requirements.txt`.
   - Integrated basic WebSocket server (`ws://localhost:8765`) into `main.py`.
   - Modified `process_stt_output` to broadcast transcripts to connected clients.

7) **Backend Testing**
   - Successfully ran `main.py`, capturing Italian audio via loopback and logging correct transcriptions.

8) **Frontend Integration & Test**
   - Connected React UI (`App.tsx`) to backend WebSocket (`ws://localhost:8765`) via `src/utils/websocket.ts`.
   - Implemented message handler (`handleNewTranscript`) to update UI state.
   - Resolved CORS and React Strict Mode connection issues (using `setTimeout` workaround - see Tech Debt).
   - Successfully displayed live Italian transcripts from Deepgram in the UI overlay.

9) **Translation Integration & Test**
   - Added `deepl` library and API key handling (`backend/translation.py`).
   - Integrated `translate_text` into backend pipeline (`main.py`).
   - Updated frontend state management (`App.tsx`) and UI (`TranscriptItem.tsx`) for English text.
   - Successfully displayed live Italian-to-English translations in the UI overlay.

## Next Steps

- **Implement LLM Suggestions**: Integrate OpenAI API (`openai`, GPT-4o mini) to generate Italian reply suggestions based on context.
  - Add `openai` library dependency.
  - Add API key to `.env`.
  - Create `backend/llm.py`.
  - Integrate into `main.py` pipeline.
  - Update WebSocket message format.
- **Update UI**: Modify frontend components (`OverlayWindow`, `App.tsx`) to display suggested replies.
- **(Future)** Add Microphone Audio Processing: Modify `main.py` to also process/send microphone audio if needed.
- **Test Italian Transcription & WebSocket Broadcast**: Run `main.py`, play Italian audio, verify correct transcription appears in logs AND is received by a test WebSocket client connected to `ws://localhost:8765`.
- **Integrate `audio.py` with `stt.py`**: Create `backend/main.py` (or similar). Consume audio chunks from `capture_audio()` and send them to the `DeepgramSTT.send_audio()` method.
- **Handle STT responses**: In `main.py`, process interim and final transcription results received from the `stt_output_queue`.
- **Update WebSocket server**: Forward transcription results to the frontend UI via the existing WebSocket connection.
- **Add Deepgram Python SDK dependency** to `backend/requirements.txt`.

## Active Decisions & Considerations

- **STT Data Format**: How to structure the data sent over the internal WebSocket to the UI (e.g., include timestamps, interim/final flags).
- **Error Handling**: How to handle Deepgram connection errors, timeouts, or API key issues. Implement reconnection logic.
- **Buffering**: How much audio data to buffer before sending to Deepgram if needed.

## Important Patterns & Preferences

- **Async pipeline** in Python 3.12 using `asyncio` Queues and coroutines.
- **Test‑driven approach**: pytest for unit/integration, SOX‑based audio regression tests.
- **IPC over WebSockets**: decouples backend capture/processing from Electron/React overlay.
- **Device discovery** by substring match in `sounddevice.query_devices()` for cross‑platform flexibility.

## Learnings & Project Insights

- Explicit device naming is crucial for reliable audio capture on Windows.
- Careful handling of asyncio event loops is required when interfacing with threaded libraries like `sounddevice`.
- **WASAPI** is the preferred host API for low-latency audio on Windows.
- **Blocksize tuning** is critical: 20 ms chunks strike the best balance between latency and throughput.
- **Device identification** will rely on matching device names like 'CABLE Output (VB-Audio Virtual Cable)' via `sounddevice.query_devices()`.
- **Deepgram SDK Handlers (`asyncwebsocket`)**: Calls handlers with the SDK client instance as the first positional argument and event data in `kwargs` (e.g., `kwargs['result']`, `kwargs['error']`). Use `*args, **kwargs` signature and `kwargs.get('key')` for robust handling.

## Technical Debt / Workarounds

- **Frontend WebSocket Connection (React Strict Mode):** The current WebSocket connection logic in `App.tsx` uses a `setTimeout` delay (100ms) within `useEffect` as a workaround for React Strict Mode's double invocation causing connection failures during development. This should be revisited to find a more robust solution that doesn't rely on timing, possibly by managing the WebSocket connection outside the component or using a dedicated library.

