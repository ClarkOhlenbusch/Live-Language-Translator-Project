# System Patterns

## System Architecture

The application follows a **two-tier architecture** comprising a Python back-end and an Electron/React front-end. The Python service captures audio streams (loopback and mic), processes them through an asynchronous pipeline (STT → Translation → LLM), and exposes results over a WebSocket server. The front-end subscribes to this server to render the real-time overlay.

## Key Technical Decisions

- **WebSocket IPC:** Chosen for cross-platform streaming of JSON events and seamless integration between Python and JavaScript.
- **Asyncio Queues:** Provide producer–consumer decoupling across capture, transcription, translation, and generation stages.
- **Device Abstraction:** Name-based lookup via `sounddevice.query_devices()` identifies necessary Windows audio devices (e.g., 'CABLE Output (VB-Audio Virtual Cable)') using WASAPI.
- **Hybrid ASR Strategy:** Default to Deepgram Nova-3 for low-latency streaming; fallback to local `faster-whisper` on GPU-equipped or offline environments.
- **Two-Phase Translation:** Use DeepL API for rapid initial translation and defer refinement to GPT-4o only when necessary.
- **Context Buffer Ring:** Maintain a fixed-size in-memory buffer of the last 3 minutes of transcript history for richer LLM prompts without re-sending older audio.

## Design Patterns in Use

- **Producer–Consumer:** Chained coroutines produce and consume data via asyncio queues (audio → STT → translation → LLM).
- **Singleton:** Global configuration loader ensures a single source of truth for API keys, device IDs, and sample rates.
- **Adapter:** Abstracts different ASR and translation services behind a common interface (`transcribe(audio_chunk)`, `translate(text)`).
- **Observer:** Front-end React components subscribe to WebSocket events and react to incoming partial and final data.
- **Ring Buffer:** Implements sliding window storage of recent transcripts and translations for context injection into LLM prompts.

## Component Relationships

- **Audio Capture Module (`backend/audio.py`):** Discovers loopback (VB-Audio Cable) and mic devices on Windows using WASAPI, opens `InputStream` instances, and pushes raw float32 frames into an asyncio queue.
- **Processing Pipeline (`backend/pipeline.py`):** Consumes audio frames, performs STT (Deepgram or Whisper), pushes transcripts to the translation worker, then to the LLM worker.
- **WebSocket Server (`backend/ws_server.py`):** Broadcasts JSON payloads containing `{ italian: ..., english: ..., replies: [...] }` to all connected front-end clients.
- **Electron/React Front-End (`ui/`):** Establishes a WebSocket client connection, updates application state stores, and renders three overlay columns (Italian transcript, English translation, reply suggestions). Handles hot-keys for toggling capture and overlay visibility.
- **Testing & Telemetry:** Uses PyTest and sox-based scripts for validating audio capture integrity. Optional Prometheus exporter and Sentry integration provide latency metrics and error reporting.

## Critical Implementation Paths

1. **Audio → STT → UI:** `capture_frames()` → `stt_queue` → `DeepgramStream` → final transcripts → `ws_server.broadcast()` → front-end render.
2. **Transcript → Translation → UI:** STT final output → `translate_queue` → DeepL API call → broadcast English text → front-end update.
3. **Context ∧ English → LLM → UI:** Maintain sliding buffer of recent transcripts, build GPT-4o prompt per new sentence, stream reply suggestions, broadcast to UI.
4. **Error & Reconnect Flow:** On audio underflow, restart capture stream; on WebSocket disconnection, exponential backoff reconnect; on API rate limit, switch to local fallback models.

