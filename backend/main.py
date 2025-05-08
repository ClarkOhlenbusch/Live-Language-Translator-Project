import asyncio
import logging
import sys
import json # For WebSocket messages
import websockets # Added for UI communication
# Removed standard queue.Queue, using asyncio.Queue
import numpy as np
from dotenv import load_dotenv # Add import

# Load environment variables from .env file
load_dotenv() # Call load_dotenv

# Configure basic logging
logging.basicConfig(
    level=logging.DEBUG, # Changed from INFO back to DEBUG for detailed logs
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s", # Added logger name
    handlers=[
        logging.StreamHandler(sys.stdout) # Log to standard output
    ]
)

try:
    from audio import capture_audio, SAMPLE_RATE
    from stt import DeepgramSTT
    from translation import translate_text
    from llm import get_llm_suggestions
except ImportError as e:
    logging.error(f"Failed to import modules. Make sure you're in the 'backend' directory and venv is active. Error: {e}")
    sys.exit(1)

# --- Configuration ---
WEBSOCKET_HOST = "localhost"
WEBSOCKET_PORT = 8765

# Default settings
default_app_settings = {
    "conversationContext": "Casual conversation with a friend.",
    "personalInfo": "My name is User. I speak English.",
    "responseLanguage": "detected",
    "userName": "User"
}

# Global application state
app_settings = default_app_settings.copy()
backend_processing_enabled = True # Global flag to control STT/LLM processing
stt_client_global = None # Will hold the DeepgramSTT instance
audio_queue_global = None # Will hold the audio queue
conversation_history = [] # Stores the last N turns
MAX_HISTORY_LENGTH = 10 # Max turns to keep in history

# --- WebSocket Server Management ---
connected_clients = set()

async def register(websocket):
    connected_clients.add(websocket)
    logging.info(f"Client connected: {websocket.remote_address}. Total: {len(connected_clients)}")

async def unregister(websocket):
    connected_clients.remove(websocket)
    logging.info(f"Client disconnected: {websocket.remote_address}. Total: {len(connected_clients)}")

async def broadcast_to_one(websocket, message_data):
    try:
        await websocket.send(json.dumps(message_data))
    except websockets.exceptions.ConnectionClosed:
        logging.warning(f"Attempted to send to a closed connection: {websocket.remote_address}")

async def broadcast_to_all(message_data):
    if connected_clients:
        message_json = json.dumps(message_data)
        tasks = [client.send(message_json) for client in connected_clients]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # Get the client corresponding to this failed task if possible
                # This is a bit indirect; ideally, we'd have a mapping
                client_list = list(connected_clients)
                if i < len(client_list):
                    logging.warning(f"Failed to send to client {client_list[i].remote_address}: {result}")
                else:
                    logging.warning(f"Failed to send to a client (index out of bounds): {result}")
    # Add warning if called with no clients
    else:
        logging.warning("broadcast_to_all called, but no clients connected.")

async def send_backend_status(websocket=None):
    """Sends the current backend processing status to a specific client or all clients."""
    status_message = {"type": "backend_status", "isActive": backend_processing_enabled}
    if websocket:
        await broadcast_to_one(websocket, status_message)
    else:
        await broadcast_to_all(status_message)

async def clear_asyncio_queue(q: asyncio.Queue):
    """Empties an asyncio.Queue."""
    while not q.empty():
        try:
            q.get_nowait()
            q.task_done() # Important if tasks are waiting on join()
        except asyncio.QueueEmpty:
            break
        except Exception as e:
            logging.warning(f"Error while clearing queue item: {e}")
            # If task_done was not called due to an error, it might be an issue for joiners
            # Depending on queue usage, might need to ensure task_done is called or handle differently
            break 
    logging.info("Asyncio queue cleared.")

async def ws_handler(websocket, path): # Path argument is conventional for websockets.serve
    global backend_processing_enabled, app_settings, stt_client_global, audio_queue_global
    await register(websocket)
    # Send initial status upon connection
    await send_backend_status(websocket)
    try:
        async for message_str in websocket:
            try:
                data = json.loads(message_str)
                message_type = data.get('type')
                
                if message_type == 'settings':
                    new_settings = data.get('settings')
                    if new_settings:
                        app_settings.update(new_settings)
                        logging.info(f"Settings updated: {app_settings}")
                
                elif message_type == 'start_processing':
                    if not backend_processing_enabled:
                        logging.info("Request received to START backend processing.")
                        backend_processing_enabled = True
                        if stt_client_global:
                            await stt_client_global.start() # Re-initializes Deepgram connection
                        # No need to restart audio capture, it runs continuously
                        await send_backend_status() # Notify all clients
                    else:
                        logging.info("Request to START processing, but already enabled.")
                        await send_backend_status(websocket) # Confirm current state to requester
                
                elif message_type == 'stop_processing':
                    if backend_processing_enabled:
                        logging.info("Request received to STOP backend processing.")
                        backend_processing_enabled = False # Set flag first

                        if stt_client_global:
                            logging.info("Telling STT client to stop...")
                            await stt_client_global.stop() # Closes Deepgram connection
                            logging.info("STT client stop command issued.")

                        if audio_queue_global:
                             logging.info("Clearing audio queue...")
                             await clear_asyncio_queue(audio_queue_global)
                             logging.info("Audio queue cleared.")

                        # Clear the STT output queue that DeepgramSTT writes to
                        # This queue is accessed via the stt_client_global instance
                        if hasattr(stt_client_global, 'output_queue') and stt_client_global.output_queue is not None:
                            logging.info("Clearing STT output queue...")
                            await clear_asyncio_queue(stt_client_global.output_queue)
                            logging.info("STT output queue cleared.")
                        else:
                            logging.warning("stt_client_global.output_queue not found or is None, cannot clear.")
                        
                        await send_backend_status() # Notify all clients
                    else:
                        logging.info("Request to STOP processing, but already disabled.")
                        await send_backend_status(websocket) # Confirm current state to requester
                
                elif message_type == 'request_backend_status':
                    await send_backend_status(websocket)
                
                else:
                    logging.info(f"Received unhandled message from {websocket.remote_address}: {data}")
            except json.JSONDecodeError:
                logging.warning(f"Received invalid JSON from {websocket.remote_address}: {message_str}")
            except Exception as e:
                logging.error(f"Error processing client message from {websocket.remote_address}: {e}", exc_info=True)
    except websockets.exceptions.ConnectionClosed:
        logging.info(f"Connection closed for {websocket.remote_address}")
    finally:
        await unregister(websocket)

# --- STT Output Processing ---
async def process_stt_output(stt_output_queue: asyncio.Queue):
    logger = logging.getLogger(__name__) # Get logger for this module
    logger.info("STT output processor started.")
    while True:
        item = None # Initialize item to None
        try:
            logger.debug("STT output processor loop top. Waiting for item...")
            item = await stt_output_queue.get()
            logger.debug(f"STT Queue Received Item. Backend enabled: {backend_processing_enabled}. Item Type: {type(item)}. Item: {str(item)[:100]}...")
            
            if not backend_processing_enabled:
                logger.debug(f"Backend processing disabled, discarding STT item: {str(item)[:100]}...")
                continue # Skip processing if backend is off

            if item is None: 
                logger.info("Received None (stop signal?) in STT output processor.")
                stt_output_queue.task_done() # Mark stop signal as done
                break # Exit the loop
            
            # Basic validation
            if not isinstance(item, dict) or 'type' not in item:
                 logger.warning(f"Received invalid item format: {str(item)[:100]}...")
                 stt_output_queue.task_done()
                 continue

            logger.info(f"Processing item: {str(item)[:100]}...")
            
            # Ensure default keys exist
            item.setdefault("english", "")
            item.setdefault("replies", [])
            item.setdefault("detected_language", "")
            
            # Check item type (adjust based on what stt.py sends)
            if item.get("type") == "transcript_data" and item.get("is_final"):
                transcript_text = item.get("transcript", "")
                if not transcript_text:
                    logger.info("Received final transcript item with empty text, skipping processing.")
                else:
                    logger.debug(f"Processing final transcript item: {item.get('transcript')[:50]}...")
                    source_text = item.get("transcript", "")
                    speaker_label = item.get("speaker", "Unknown Speaker")
                    
                    # Add to history only if there is actual text
                    if source_text:
                        turn = {"speaker": speaker_label, "original": source_text, "english": ""}
                        conversation_history.append(turn)
                        # Trim history
                        if len(conversation_history) > MAX_HISTORY_LENGTH:
                            conversation_history.pop(0)
                    
                        try:
                            english_translation, detected_lang_code = await translate_text(source_text, return_detected_lang=True)
                        except Exception as translate_err:
                            logger.error(f"Error during translation: {translate_err}", exc_info=True)
                            english_translation = None
                            detected_lang_code = "error"

                        if english_translation is not None:
                            item["english"] = english_translation
                            item["detected_language"] = detected_lang_code
                            
                            if conversation_history:
                                conversation_history[-1]["english"] = english_translation
                                
                            try:
                                suggestions = await get_llm_suggestions(
                                    english_text=english_translation,
                                    user_settings=app_settings,
                                    detected_language=detected_lang_code,
                                    history=conversation_history
                                )
                            except Exception as llm_err:
                                logger.error(f"Error getting LLM suggestions: {llm_err}", exc_info=True)
                                suggestions = ["LLM Error"] # Provide error indicator
                                
                            if suggestions is not None:
                                item["replies"] = suggestions
                            else:
                                 logger.warning(f"LLM suggestion returned None for: {english_translation}")
                                 item["replies"] = ["LLM Issue"] # Provide issue indicator
                        else:
                            logger.warning(f"Translation failed or returned None for: {source_text}")
                            item["english"] = "Translation Error"
                            item["detected_language"] = "error"
                            item["replies"] = ["Translation Failed"]
                    else:
                        logger.debug("Received final transcript item with empty text, skipping T/LLM.")
            else:
                # Handle other item types or non-final transcripts if necessary
                logger.debug(f"Received non-final or non-'transcript_data' item type: {item.get('type')}, skipping further processing.")
                # Even if not processing further, broadcast the raw item for potential UI updates (like interim results)
                # Make sure necessary fields exist before broadcasting
                broadcast_item = { # Construct a minimal item for broadcasting
                    "type": item.get("type"),
                    "is_final": item.get("is_final"),
                    "transcript": item.get("transcript"),
                    "speaker": item.get("speaker"),
                    "detected_language": item.get("detected_language"),
                    "english": item.get("english"),
                    "replies": item.get("replies", [])
                }
                await broadcast_to_all(broadcast_item)

            # Broadcast regardless of processing result (errors included)
            logger.info(f"Broadcasting item: {str(item)[:100]}...")
            await broadcast_to_all(item)
            logger.info(f"Broadcast complete for item: {str(item)[:100]}.")
            
            # Mark task as done *after* all processing and broadcasting
            stt_output_queue.task_done()

        except asyncio.CancelledError:
            logger.info("STT output processor cancelled.")
            # If an item was retrieved before cancellation, mark it done
            if item is not None:
                 try:
                     stt_output_queue.task_done()
                     logger.debug("Marked item done during cancellation.")
                 except ValueError:
                     pass # Already done
                 except Exception as inner_e:
                     logger.error(f"Error calling task_done during cancellation: {inner_e}")
            break # Exit the loop
        except Exception as e:
            logger.error(f"Unhandled error in STT output processor loop: {e}", exc_info=True)
            # Ensure task_done is called if an item was retrieved before the error
            if item is not None:
                 try:
                     stt_output_queue.task_done()
                     logger.debug("Marked item done after unhandled exception.")
                 except ValueError:
                     pass # Already done
                 except Exception as inner_e:
                     logger.error(f"Error calling task_done after unhandled exception: {inner_e}")
            # Optional: Add a small sleep to prevent potential fast error loops
            await asyncio.sleep(0.1)

    logger.info("STT output processor finished.")

# --- Audio Sending Task ---
async def send_audio_to_stt(audio_q: asyncio.Queue, stt_c: DeepgramSTT):
    logging.info("Audio sending task started.")
    while True:
        try:
            if not backend_processing_enabled:
                await asyncio.sleep(0.1) # Sleep briefly to avoid busy-waiting when off
                continue
                
            audio_bytes = await audio_q.get()
            if audio_bytes is None: 
                logging.info("Received stop signal for audio sending task.")
                break
            if stt_c and backend_processing_enabled: # Double check if stt_client is active
                 await stt_c.send_audio(audio_bytes)
            audio_q.task_done()
        except asyncio.CancelledError:
            logging.info("Audio sending task cancelled.")
            break
        except Exception as e:
            logging.error(f"Error sending audio to STT: {e}", exc_info=True)
    logging.info("Audio sending task finished.")

async def main():
    global stt_client_global, audio_queue_global
    logging.info("Starting application...")
    
    audio_queue_global = asyncio.Queue(maxsize=100) # Max buffer 100 * 20ms = 2 seconds
    stt_output_queue = asyncio.Queue()

    stt_client_global = DeepgramSTT(stt_output_queue)

    allowed_origins = ["http://localhost:5173"]
    logging.info(f"Starting WebSocket server on {WEBSOCKET_HOST}:{WEBSOCKET_PORT}")
    
    # Start the server and get the server object
    server = await websockets.serve(
        ws_handler, 
        WEBSOCKET_HOST, 
        WEBSOCKET_PORT, 
        origins=allowed_origins
    )
    logging.info("WebSocket server started.")

    # Start other background tasks
    if backend_processing_enabled:
        await stt_client_global.start()
        
    capture_task = asyncio.create_task(capture_audio(audio_queue_global))
    send_task = asyncio.create_task(send_audio_to_stt(audio_queue_global, stt_client_global))
    process_task = asyncio.create_task(process_stt_output(stt_output_queue))
    
    # Keep the main function running by waiting for tasks 
    # (server runs in the background managed by websockets library)
    running_tasks = [capture_task, send_task, process_task]
    logging.info("All main background tasks started.")

    try:
        # Wait for tasks to complete (they run indefinitely until cancelled)
        await asyncio.gather(*running_tasks)
    except KeyboardInterrupt:
        logging.info("Keyboard interrupt received, shutting down...")
    except asyncio.CancelledError:
        logging.info("Main task cancelled, shutting down...") # Handle cancellation of main
    finally:
        logging.info("Initiating shutdown...")
        
        # 1. Close the WebSocket server first to prevent new connections
        if server:
            server.close()
            await server.wait_closed()
            logging.info("WebSocket server closed.")

        # 2. Cancel background tasks
        for task in running_tasks:
            if task and not task.done():
                task.cancel()
        
        # Wait for cancellations
        await asyncio.gather(*running_tasks, return_exceptions=True)
        logging.info("Background tasks cancelled.")

        # 3. Stop the STT client if it exists
        if stt_client_global:
            logging.info("Stopping Deepgram client...")
            await stt_client_global.stop()
        
        logging.info("Application shut down gracefully.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Application interrupted by user. Exiting.")
    except Exception as e:
        logging.critical(f"Unhandled exception in main entry point: {e}", exc_info=True)