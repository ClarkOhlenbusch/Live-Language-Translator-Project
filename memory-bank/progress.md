## Here we are going to log all our updates we make as we develop this app - be detailed.

1) Create inital UI, currently using mockData.ts for fake data to simulate a real use. (will be replaced with real data from system audio.)
 1.1 - small change made so new chats apear on top and push the rest of the previous questions down, so most relevant info is on top always.
2) Setup monorepo structure and initial backend
 2.1 - Created backend directory with Python WebSocket server
 2.2 - Added WebSocket client utility in frontend
 2.3 - Updated package.json with new dependencies and scripts
 2.4 - Added requirements.txt for Python dependencies
3) Implement Audio Loopback Proof (Windows)
 3.1 - Created backend/audio.py to capture VB-Audio Cable (loopback) and default microphone using sounddevice and WASAPI.
 3.2 - Implemented device discovery logic using specific names for robustness.
 3.3 - Resolved threading issues with asyncio event loops in sounddevice callbacks using functools.partial.
 3.4 - Verified script successfully captures and yields 20ms chunks from both streams.
4) Implement Deepgram STT Integration (`backend/stt.py`)
 4.1 - Added `deepgram-python-sdk` to requirements.
 4.2 - Created `DeepgramSTT` class using `asyncwebsocket` interface.
 4.3 - Implemented connection logic (`start`, `stop`, `_connect`, `_disconnect`) with state tracking (`_is_connected`).
 4.4 - Corrected event handler function signatures (`_on_open`, `_on_metadata`, etc.) to match SDK expectations, resolving `TypeError` issues.
 4.5 - Tested `stt.py` directly; confirmed connection opens, handlers receive events, and closes cleanly.
5) Integrate Audio Capture and STT (`backend/main.py`)
 5.1 - Created initial `main.py` structure.
 5.2 - Modified `main.py` to let `audio.py` handle device discovery internally.
 5.3 - Corrected import errors (`find_audio_devices`, `BLOCKSIZE` vs `CHUNK_SIZE`).
 5.4 - Successfully ran `main.py`, capturing system audio via loopback, sending to Deepgram, and receiving/logging transcripts.
6) Establish Backend WebSocket Server for UI Communication
 6.1 - Added `websockets` library to requirements.txt.
 6.2 - Implemented WebSocket server logic in `main.py` (`register`, `unregister`, `broadcast`, `ws_handler`).
 6.3 - Modified `process_stt_output` to send transcripts to connected UI clients via `broadcast`.
7) Configure for Italian Transcription & Test
 7.1 - Updated `LiveOptions` in `stt.py` to `language="it"`, `model="nova-2"`, `smart_format=True`.
 7.2 - Successfully ran `main.py`, capturing Italian audio via loopback and logging correct transcriptions.
8) Connect Frontend UI to Backend WebSocket
 8.1 - Identified relevant UI files (`src/App.tsx`, `src/utils/websocket.ts`).
 8.2 - Implemented WebSocket connection logic in `src/utils/websocket.ts` and `src/App.tsx`.
 8.3 - Updated UI state (`transcriptData`) and `App.tsx` component to display received transcripts.
 8.4 - Resolved frontend WebSocket connection stability issues (CORS, React Strict Mode workaround using `setTimeout`).
 8.5 - Successfully tested end-to-end flow: Audio -> STT -> Backend WS -> Frontend WS -> UI Display.
9) Add Translation Service
 9.1 - Added `deepl` client library (`deepl`) to `backend/requirements.txt`.
 9.2 - Created `backend/translation.py` with `translate_text` function using DeepL API.
 9.3 - Integrated translation step into `main.py`'s `process_stt_output` task.
 9.4 - Updated WebSocket message format and frontend (`App.tsx`, `TranscriptItem.tsx`) to display English translation.
 9.5 - Successfully tested end-to-end flow including translation.
10) Add LLM Reply Suggestions
 10.1 - TODO: Add OpenAI client library (`openai`) to `backend/requirements.txt`.
 10.2 - TODO: Get OpenAI API key into `.env` file.
 10.3 - TODO: Create `backend/llm.py` with a function to call GPT-4o mini.
 10.4 - TODO: Integrate LLM step into `main.py` pipeline (after translation).
 10.5 - TODO: Update WebSocket message format and frontend to display suggestions.