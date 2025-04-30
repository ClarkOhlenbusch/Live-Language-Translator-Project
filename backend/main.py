import asyncio
import logging
import sys
import json # For WebSocket messages
import websockets # Added for UI communication
from queue import Queue # Using standard queue for simplicity initially
import numpy as np

# Configure basic logging
logging.basicConfig(
    level=logging.INFO, # Adjust level as needed (DEBUG, INFO, WARNING, ERROR)
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout) # Log to standard output
    ]
)

try:
    # Import capture_audio and constants, but not find_audio_devices directly
    # BLOCKSIZE was renamed to CHUNK_SIZE in audio.py, and isn't needed here anyway
    from audio import capture_audio, SAMPLE_RATE
    from stt import DeepgramSTT
    from translation import translate_text # <--- Import the new function
    from llm import get_llm_suggestions # <--- Import the new function
except ImportError as e:
    logging.error(f"Failed to import modules. Make sure you're in the 'backend' directory and venv is active. Error: {e}")
    sys.exit(1)

# --- Configuration ---
WEBSOCKET_HOST = "localhost"
WEBSOCKET_PORT = 8765 # Standard port for WebSocket example
# Device finding is now handled within audio.py's capture_audio

# --- WebSocket Server Management ---
connected_clients = set()

async def register(websocket):
    """Adds a new client to the set of connected clients."""
    connected_clients.add(websocket)
    logging.info(f"Client connected: {websocket.remote_address}. Total clients: {len(connected_clients)}")

async def unregister(websocket):
    """Removes a client from the set."""
    connected_clients.remove(websocket)
    logging.info(f"Client disconnected: {websocket.remote_address}. Total clients: {len(connected_clients)}")

async def broadcast(message):
    """Sends a message (JSON string) to all connected clients."""
    if connected_clients:
        # Prepare message (ensure it's a JSON string)
        message_json = json.dumps(message)
        # Create tasks for sending to all clients concurrently
        tasks = [client.send(message_json) for client in connected_clients]
        # Wait for all sends to complete (or handle potential errors)
        await asyncio.gather(*tasks, return_exceptions=True) # Log exceptions if send fails

async def ws_handler(websocket):
    """Handles incoming WebSocket connections."""
    await register(websocket)
    try:
        # Keep the connection alive, handling potential messages from client if needed
        async for message in websocket:
            # For now, just log messages received from client
            logging.info(f"Received message from {websocket.remote_address}: {message}")
            # We could add logic here to handle client commands (e.g., pause/resume)
            pass
    except websockets.exceptions.ConnectionClosedOK:
        logging.info(f"Connection closed OK for {websocket.remote_address}")
    except websockets.exceptions.ConnectionClosedError as e:
        logging.warning(f"Connection closed with error for {websocket.remote_address}: {e}")
    finally:
        await unregister(websocket)

# --- STT Output Processing ---

async def process_stt_output(stt_output_queue: asyncio.Queue):
    """Consumes items from the STT queue, translates, gets suggestions, and broadcasts."""
    logging.info("STT output processor started.")
    while True:
        try:
            item = await stt_output_queue.get()
            if item is None: # Sentinel value to stop
                logging.info("Received stop signal for STT output processor.")
                break
            
            # Initialize fields for translation and replies
            item["english"] = ""
            item["replies"] = []

            # --- Add Translation Step ---
            if item.get("type") == "transcript" and item.get("transcript"):
                italian_text = item["transcript"]
                logging.debug(f"Attempting to translate: {italian_text}")
                english_translation = await translate_text(italian_text)
                if english_translation is not None:
                    item["english"] = english_translation
                    logging.debug(f"Translation successful: {english_translation}")

                    # --- Add LLM Suggestion Step (only if translation succeeded) ---
                    logging.debug(f"Attempting to get LLM suggestions for: {english_translation}")
                    suggestions = await get_llm_suggestions(english_translation)
                    if suggestions is not None:
                        item["replies"] = suggestions
                        logging.debug(f"LLM suggestions successful: {suggestions}")
                    else:
                         logging.warning(f"LLM suggestion failed for: {english_translation}")
                    # ----------------------------------------------------------

                else:
                    logging.warning(f"Translation failed for: {italian_text}")
            # ---------------------------

            logging.info(f"Processed STT Output (with translation & LLM attempt): {item}")
            # Forward the potentially fully populated item
            await broadcast(item)
            stt_output_queue.task_done()
        except asyncio.CancelledError:
            logging.info("STT output processor cancelled.")
            break
        except Exception as e:
            logging.error(f"Error processing STT output: {e}", exc_info=True)
    logging.info("STT output processor finished.")

# --- Audio Sending Task ---
async def send_audio_to_stt(audio_queue: asyncio.Queue, stt_client: DeepgramSTT):
    """Consumes audio chunks from the queue and sends them to the STT client."""
    logging.info("Audio sending task started.")
    while True:
        try:
            audio_bytes = await audio_queue.get()
            if audio_bytes is None: # Sentinel value to stop (optional)
                logging.info("Received stop signal for audio sending task.")
                break
            await stt_client.send_audio(audio_bytes)
            audio_queue.task_done()
        except asyncio.CancelledError:
            logging.info("Audio sending task cancelled.")
            break
        except Exception as e:
            logging.error(f"Error sending audio to STT: {e}")
            # Decide if we should break the loop on error or continue
            # break # Uncomment to stop on error
    logging.info("Audio sending task finished.")

async def main():
    """Main function to capture audio, send to STT, and run WebSocket server."""
    logging.info("Starting application...")
    audio_queue = asyncio.Queue()
    stt_output_queue = asyncio.Queue()

    # Configure Deepgram STT
    stt_client = DeepgramSTT(stt_output_queue)

    # Start the WebSocket server
    allowed_origins = ["http://localhost:5173"]
    logging.info(f"Starting WebSocket server on {WEBSOCKET_HOST}:{WEBSOCKET_PORT}, allowing origins: {allowed_origins}")
    start_server = await websockets.serve(
        ws_handler,
        WEBSOCKET_HOST,
        WEBSOCKET_PORT,
        origins=allowed_origins
    )
    logging.info("WebSocket server started.")

    # Start Deepgram connection, audio capture, audio sending, and STT processing concurrently
    stt_task = asyncio.create_task(stt_client.start())
    capture_task = asyncio.create_task(capture_audio(audio_queue))
    send_task = asyncio.create_task(send_audio_to_stt(audio_queue, stt_client))
    process_task = asyncio.create_task(process_stt_output(stt_output_queue))

    # Wait for tasks to complete
    try:
        # Gather all essential tasks
        await asyncio.gather(capture_task, send_task, stt_task, process_task)
    except KeyboardInterrupt:
        logging.info("Keyboard interrupt received, shutting down...")
    finally:
        # Cleanly stop tasks (in reverse order of dependency might be good)
        logging.info("Stopping audio capture (cancelling task)...")
        capture_task.cancel()
        try:
            await capture_task
        except asyncio.CancelledError:
            logging.info("Audio capture task cancelled.")

        logging.info("Stopping audio sending task (cancelling task)...")
        send_task.cancel()
        try:
            await send_task
        except asyncio.CancelledError:
            logging.info("Audio sending task cancelled.")

        logging.info("Stopping Deepgram client...")
        await stt_client.stop()

        logging.info("Stopping STT output processing (cancelling task)...")
        process_task.cancel()
        try:
            await process_task
        except asyncio.CancelledError:
            logging.info("STT output processing task cancelled.")

        # Stop the WebSocket server
        logging.info("Closing WebSocket server...")
        start_server.close()
        await start_server.wait_closed()
        logging.info("WebSocket server closed.")
        logging.info("Application shut down gracefully.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Application interrupted by user. Exiting.")
    except Exception as e:
        logging.critical(f"Unhandled exception in main entry point: {e}", exc_info=True)