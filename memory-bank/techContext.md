# Tech Context

## Technologies Used

- **Languages:** Python 3.12, TypeScript
- **Frameworks/Libraries:**
  - Backend: `sounddevice`, `asyncio`, `websockets`, `soundfile`, `pytest`
  - Frontend: Electron, React, Tailwind CSS, `ws` (WebSocket client)
- **APIs/Services:** Deepgram Nova-3 (ASR), Whisper (local fallback), DeepL API (translation), OpenAI GPT-4o mini (LLM)
- **Tools:** VB-Audio Cable (Windows), BlackHole (macOS), ALSA `snd_aloop` + PulseAudio (Linux), SOX (audio testing)
- **Packaging/CI:** PyInstaller, Electron Builder, GitHub Actions, Sentry (optional)

## Development Setup

1. **Clone repository:**
   ```bash
   git clone <repo-url> && cd <repo>
   ```
2. **Backend dependencies:**
   ```bash
   cd backend
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
3. **Frontend dependencies:**
   ```bash
   cd ui
   npm install
   ```
4. **Virtual audio drivers:**
   - **Windows:** Install VB-Audio Cable, configure Playback → “CABLE Input” and Recording → “Listen to this device” on “CABLE Output”
   - **macOS:** Install BlackHole 2-ch, create a Multi-Output device in Audio MIDI Setup
5. **Environment variables:**
   ```bash
   export DEEPGRAM_API_KEY=<key>
   export DEEPL_API_KEY=<key>
   export OPENAI_API_KEY=<key>
   ```
6. **Run dev servers:**
   - **Backend:** `cd backend && source venv/bin/activate && python ws_server.py`
   - **Frontend:** `cd ui && npm run start`

## Technical Constraints

- **Latency:** End-to-end round-trip ≤ 1.5 seconds
- **API Budget:** ≤ US $20 monthly (Deepgram + DeepL + GPT-4o usage)
- **OS Compatibility:** Windows 10/11, macOS 11+
- **Hardware:** GPU (optional for Whisper fallback), minimum 8 GB RAM
- **Audio Blocksize:** 20 ms chunks (960 samples at 48 kHz)

## Dependencies

- **ASR:** Deepgram Nova-3 streaming, Whisper-v3 (faster-whisper) local
- **Translation:** DeepL API Pro
- **LLM:** OpenAI GPT-4o mini streaming
- **Audio drivers:** VB-Audio Cable (Windows), BlackHole (macOS)
- **Testing:** SOX for audio, PyTest for unit/integration
- **CI/CD:** GitHub Actions, optional Sentry for error reporting

## Tool Usage Patterns

- **Linters:** `black` + `flake8` for Python, `ESLint` + `Prettier` for TypeScript
- **Debugging:**
  - Python: `logging` module at DEBUG level, interactive REPL
  - Frontend: Chrome DevTools, React DevTools
- **CI/CD Workflow:**
  - On push to `main`: run lint, tests, build artifacts
  - On tag/release: generate installers via GitHub Actions using PyInstaller and Electron Builder
- **Telemetry:** Expose Prometheus metrics endpoint in backend; use Sentry SDK to capture exceptions

