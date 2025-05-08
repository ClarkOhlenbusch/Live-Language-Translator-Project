# Live Language Translator

A real-time language translator that automatically transcribes spoken language, translates it to English, and suggests relevant replies.

## Features

- **Multilingual Support**: Automatically detects and transcribes multiple languages using Deepgram's nova-3 model
- **Real-time Translation**: Instantly translates spoken words to English
- **Contextual Reply Suggestions**: Provides personalized response suggestions in the detected language
- **Customizable Settings**: Configure conversation context, personal details, and response language preferences
- **Always-on-top Window**: Overlay window stays visible above other applications
- **One-click Launcher**: Simple batch/shell script to start the entire application

## Supported Languages

The application supports the following languages via Deepgram's multilingual model:
- English
- Spanish
- French
- German
- Hindi
- Russian
- Portuguese
- Japanese
- Italian
- Dutch

## Customization Options

### Personal Context
Add information about yourself to get more personalized and contextually appropriate suggestions:
- Name, profession, languages spoken
- Personal background and interests
- Specific topics you want to discuss

### Conversation Context
Choose from various conversation types or create your own:
- Casual conversations
- Business meetings
- Academic lectures
- Travel conversations
- Medical appointments
- Technical discussions

### Response Language
- **Match Detected**: AI responds in the same language as detected in the conversation
- **Always English**: AI always provides English responses regardless of the conversation language

## Prerequisites

- [Python](https://www.python.org/downloads/) (3.7 or higher)
- [Node.js](https://nodejs.org/) (16 or higher)
- API keys:
  - [Deepgram](https://deepgram.com/) (for speech-to-text)
  - [DeepL](https://www.deepl.com/) (for translation)
  - [OpenAI](https://openai.com/) (for reply suggestions)

## Quick Start

### First-time Setup

1. Clone this repository
2. Create a `.env` file in the root directory with your API keys:
   ```
   DEEPGRAM_API_KEY=your_deepgram_key
   DEEPL_API_KEY=your_deepl_key
   OPENAI_API_KEY=your_openai_key
   ```
3. Run the setup script:
   ```
   # Windows
   run-app.bat --setup
   
   # macOS/Linux
   ./run-app.sh --setup
   ```

### Running the Application

Simply double-click:
- `run-app.bat` (on Windows)
- `run-app.sh` (on macOS/Linux)

Or run via terminal:
```
# Windows
.\run-app.bat

# macOS/Linux
./run-app.sh
```

## Development

### Project Structure

- `backend/` - Python backend for audio capture, STT, and translation
- `src/` - React frontend for the overlay UI
- `scripts/` - Setup and utility scripts
- `electron.cjs` - Electron configuration for overlay window

### Development Commands

```bash
# Install dependencies
npm install
cd backend && pip install -r requirements.txt

# Start UI only (React)
npm run start:ui

# Start backend only (Python)
npm run start:backend

# Start complete application (UI + Backend + Electron)
npm start
```