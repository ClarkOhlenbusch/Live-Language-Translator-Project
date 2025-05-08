import asyncio
import logging
import os

from dotenv import load_dotenv
from deepgram import (
    DeepgramClient, DeepgramClientOptions,
    LiveTranscriptionEvents,
    LiveOptions,
)

load_dotenv() # Load environment variables from .env file

API_KEY = os.getenv("DEEPGRAM_API_KEY")
if not API_KEY:
    # For development/testing, try using a fallback key (NOT RECOMMENDED FOR PRODUCTION)
    logging.warning("No DEEPGRAM_API_KEY in .env file. API access will likely fail.")

# URL for the realtime streaming audio endpoint
URL = "wss://api.deepgram.com/v1/listen"

# Deepgram client configuration
config: DeepgramClientOptions = DeepgramClientOptions(
    verbose=logging.INFO,
    # Add keepalive option if needed later for long pauses
    # options={"keepalive": "true"}
)

# Deepgram connection options (Updated for multilingual support)
options: LiveOptions = LiveOptions(
    model="nova-3",       # Use Nova-3 model (instead of nova-2)
    language="multi",     # Set to multilingual mode
    smart_format=True,    # Enable smart formatting
    encoding="linear16",
    sample_rate=48000,
    channels=1,
    diarize=True          # Enable speaker diarization
)

class DeepgramSTT:
    """Manages the connection to Deepgram and processes STT events."""

    def __init__(self, output_queue: asyncio.Queue):
        self.output_queue = output_queue
        self.dg_client = DeepgramClient(API_KEY, config)
        self.dg_connection = self.dg_client.listen.asyncwebsocket.v("1")
        self._connection_lock = asyncio.Lock()
        self._task = None
        self._is_connected = False # Add connection state flag
        # Register handlers once during initialization
        self._register_handlers()
        logging.info("DeepgramSTT initialized and handlers registered.")

    async def start(self):
        """Starts the Deepgram connection and event handling task."""
        # Handlers are now registered in __init__, no need to call here
        # self._register_handlers()
        if self._task is None:
            # Create the task that runs the main connection/reconnection loop
            self._task = asyncio.create_task(self._run())
            logging.info("DeepgramSTT main processing task started.")
        else:
            # If start is called again while already running, ensure connection is attempted
            # The _run loop handles reconnections if _is_connected is False
            logging.warning("DeepgramSTT task already running. Ensure connection is active if needed.")
            # Optionally, trigger a connection check/attempt within the existing _run loop
            # This might involve setting an event or directly calling _connect if safe
            # For now, rely on the _run loop's polling mechanism

    async def stop(self):
        """Stops the Deepgram connection and the event handling task."""
        if self._task:
            logging.info("Stopping DeepgramSTT task...")
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                logging.info("DeepgramSTT task cancelled successfully.")
            finally:
                self._task = None
                # Ensure connection is closed if task cancellation didn't trigger _disconnect
                # This might be redundant if _run's finally block always runs
                if self._is_connected:
                    logging.warning("Task cancelled, explicitly ensuring disconnection.")
                    await self._disconnect()
        else:
            logging.info("DeepgramSTT task not running.")

    async def _connect(self):
        """Establishes connection to Deepgram."""
        async with self._connection_lock:
            # Reset connected flag before attempting connection
            self._is_connected = False
            try:
                # Start the connection using the options
                await self.dg_connection.start(options)
                logging.info("Deepgram connection start initiated.")
                # Note: Connection might not be fully open until _on_open callback fires
                return True
            except Exception as e:
                logging.error(f"Could not start Deepgram connection: {e}")
                self._is_connected = False # Ensure flag is false on error
                return False

    async def _disconnect(self):
        """Closes the Deepgram connection."""
        async with self._connection_lock:
            if self.dg_connection:
                logging.info("Closing Deepgram connection...")
                try:
                    # Use finish() for asyncwebsocket interface
                    await self.dg_connection.finish()
                    logging.info("Deepgram connection finished.")
                except Exception as e:
                    logging.error(f"Error finishing Deepgram connection: {e}")
                finally:
                    self._is_connected = False # Ensure flag is false after finish/error
            else:
                 logging.debug("Attempted to disconnect, but no active connection object.")

    def _register_handlers(self):
        """Registers event handlers for the Deepgram connection."""
        # Register handlers directly on the connection object created in __init__
        self.dg_connection.on(LiveTranscriptionEvents.Open, self._on_open)
        # Use LiveTranscriptionEvents.Transcript; the payload will contain all result details
        self.dg_connection.on(LiveTranscriptionEvents.Transcript, self._on_message)
        self.dg_connection.on(LiveTranscriptionEvents.Metadata, self._on_metadata)
        self.dg_connection.on(LiveTranscriptionEvents.SpeechStarted, self._on_speech_started)
        self.dg_connection.on(LiveTranscriptionEvents.UtteranceEnd, self._on_utterance_end)
        self.dg_connection.on(LiveTranscriptionEvents.Error, self._on_error)
        self.dg_connection.on(LiveTranscriptionEvents.Close, self._on_close)
        logging.debug("Deepgram event handlers registered.")

    async def send_audio(self, audio_chunk: bytes):
        """Sends an audio chunk to Deepgram if connected."""
        if self._is_connected and self.dg_connection:
            try:
                await self.dg_connection.send(audio_chunk)
            except Exception as e:
                logging.error(f"Error sending audio to Deepgram: {e}")
                # Decide on error handling: reconnect, log, raise?
                # Setting flag to false, _run loop might attempt reconnect
                self._is_connected = False
        elif not self._is_connected:
             logging.log(logging.DEBUG - 5, "Cannot send audio: Not connected.") # Reduce log noise
        # else: # Should not happen if _is_connected implies dg_connection exists
        #     logging.warning("Cannot send audio: Connection object missing but connected flag true?")

    # --- Event Handlers ---

    async def _on_open(self, *args, **kwargs):
        # Preserve original kwargs for logging, but extract 'open' if present
        open_payload = kwargs.get('open', args[0] if args else None) # Deepgram SDK might pass payload as first arg if not in kwargs
        logging.info(f"Deepgram connection opened. Payload: {open_payload}, All Args: {args}, All Kwargs: {kwargs}")
        self._is_connected = True # Set connected flag

    async def _on_message(self, *args, **kwargs):
        # It's safer to expect 'result' as the primary payload, often the first arg if not in kwargs.
        # The Deepgram SDK's emit for Results is typically `emit(Results, result=payload)`
        # or for other events like Open, it might be `emit(Open, open=payload)`
        # For registered instance methods, the first arg to the method (after self) is the payload.

        logging.debug(f"STT _on_message ENTERED. Args: {args}, Kwargs: {list(kwargs.keys())}")

        result_payload = None
        if 'result' in kwargs: # Explicit 'result' kwarg, typical for Results event
            result_payload = kwargs['result']
        elif args: # Payload might be the first positional argument
            result_payload = args[0]

        if not result_payload:
            logging.warning(f"_on_message: No result payload found in args or kwargs. Args: {args}, Kwargs: {kwargs}")
            return

        logging.debug(f"STT _on_message: Received payload type: {type(result_payload)}")

        try:
            # Ensure the payload is the expected LiveTranscriptionResponse object
            # (or whatever type Deepgram sends for LiveTranscriptionEvents.Results)
            if not hasattr(result_payload, 'type') or not hasattr(result_payload, 'channel'):
                logging.warning(f"_on_message: Payload does not look like a standard Deepgram response. Payload: {str(result_payload)[:500]}")
                return

            logging.debug(f"STT _on_message: Event type from payload: {result_payload.type}")

            # This debug line should now trigger for all 'Results' events if diarize is on.
            if options.diarize:
                # Convert to dict for full JSON-like logging if it's a complex object
                try:
                    # Assuming result_payload is a Pydantic model or similar that can be dict()-ed
                    loggable_result = result_payload.to_dict() if hasattr(result_payload, 'to_dict') else str(result_payload)
                    logging.debug(f"Diarized Result Received (raw): {loggable_result}")
                except Exception as log_e:
                    logging.error(f"Error converting result_payload to loggable string/dict: {log_e}")
                    logging.debug(f"Diarized Result Received (raw, str fallback): {str(result_payload)}")

            if not hasattr(result_payload.channel, 'alternatives') or not result_payload.channel.alternatives:
                logging.warning("_on_message: Results payload missing channel.alternatives.")
                return

            primary_alternative = result_payload.channel.alternatives[0]
            transcript = getattr(primary_alternative, 'transcript', '')
            confidence = getattr(primary_alternative, 'confidence', 0.0)
            words = getattr(primary_alternative, 'words', [])
            
            is_final = getattr(result_payload, 'is_final', False)
            speech_final = getattr(result_payload, 'speech_final', False) # Important for knowing end of speech segment

            logging.info(f"STT _on_message: Processing transcript='{transcript[:50]}...', is_final={is_final}, speech_final={speech_final}")

            # Determine speaker and language
            detected_language_code = "und"
            if hasattr(primary_alternative, 'languages') and primary_alternative.languages:
                detected_language_code = primary_alternative.languages[0]

            speaker_id = 0 # Default speaker
            # Diarization provides speaker per word, consolidate this.
            # Simplistic: use the first word's speaker, or majority, or track segments.
            if words and hasattr(words[0], 'speaker'):
                speaker_id = words[0].speaker
            
            # Construct the data to be queued for main.py
            # Only queue if it's a meaningful final transcript or a speech_final signal
            if is_final and (transcript or speech_final):
                logging.info(f"STT _on_message: Preparing to queue final data. Transcript: '{transcript[:50]}...', Lang: {detected_language_code}, Speaker: {speaker_id}")
                await self.output_queue.put({
                    "type": "transcript_data", # More descriptive type for main.py
                    "is_final": is_final,
                    "speech_final": speech_final, # Pass this through
                    "transcript": transcript,
                    "confidence": confidence,
                    "speaker_id": speaker_id, # Use a consistent key
                    "language_code": detected_language_code,
                    "words": [word.to_dict() for word in words if hasattr(word, 'to_dict')] # Ensure words can be dict
                })
                logging.info(f"STT _on_message: Queued item. Queue size: {self.output_queue.qsize()}")
            elif not is_final and transcript: # Interim results with content
                logging.debug(f"STT _on_message: Interim transcript: '{transcript[:50]}...'. Not queuing yet.")
            else:
                logging.debug(f"STT _on_message: Non-final empty or non-speech_final empty result. Not queuing.")

        except AttributeError as ae:
            logging.error(f"_on_message: AttributeError accessing result payload: {ae}", exc_info=True)
            logging.error(f"Problematic payload snippet: {str(result_payload)[:500]}")
        except Exception as e:
            logging.error(f"_on_message: General error processing STT message: {e}", exc_info=True)
            if 'result_payload' in locals() and result_payload is not None:
                 logging.error(f"Full problematic payload: {str(result_payload)}")
            else:
                 logging.error(f"Error occurred before result_payload was assigned or was None.")

    async def _on_metadata(self, *args, **kwargs):
        metadata_payload = kwargs.get('metadata', args[0] if args else None)
        logging.debug(f"Received metadata. Payload: {metadata_payload}, All Args: {args}, All Kwargs: {kwargs}")

    async def _on_speech_started(self, *args, **kwargs):
        speech_started_payload = kwargs.get('speech_started', args[0] if args else None)
        logging.debug(f"Speech started event. Payload: {speech_started_payload}, All Args: {args}, All Kwargs: {kwargs}")

    async def _on_utterance_end(self, *args, **kwargs):
        utterance_end_payload = kwargs.get('utterance_end', args[0] if args else None)
        logging.debug(f"Utterance end event. Payload: {utterance_end_payload}, All Args: {args}, All Kwargs: {kwargs}")

    async def _on_error(self, *args, **kwargs):
        error_payload = kwargs.get('error', args[0] if args else None)
        logging.error(f"Deepgram error event. Error: {error_payload}, All Args: {args}, All Kwargs: {kwargs}")
        self._is_connected = False # Set connected flag to false

    async def _on_close(self, *args, **kwargs):
        close_payload = kwargs.get('close', args[0] if args else None)
        logging.info(f"Deepgram connection closed event. Payload: {close_payload}, All Args: {args}, All Kwargs: {kwargs}")
        self._is_connected = False # Set connected flag to false

    async def _run(self):
        """Main task loop to establish connection and keep it alive."""
        logging.info("Starting Deepgram STT run loop.")
        # Initial connection attempt
        if not await self._connect():
            logging.error("Failed to start Deepgram connection initially. Task exiting.")
            return

        try:
            while True:
                # Check connection status via our flag
                if not self._is_connected:
                     logging.warning("Deepgram connection appears closed. Attempting to reconnect...")
                     await asyncio.sleep(5) # Wait before reconnecting
                     if not await self._connect():
                         logging.error("Reconnect failed. Will retry later.")
                         await asyncio.sleep(10)
                     # If _connect succeeds, the _on_open handler will set _is_connected = True
                else:
                    # Connection seems okay, sleep and check later
                    await asyncio.sleep(5)
        except asyncio.CancelledError:
            logging.info("Deepgram run loop cancelled.")
        except Exception as e:
             logging.error(f"Error in Deepgram run loop: {e}")
        finally:
             await self._disconnect()
             logging.info("Deepgram run loop finished.")

# --- Example Usage (for testing this module directly) ---
async def main():
    # Example: Read audio from a file and send it
    # Replace with actual audio stream in the main application
    stt_output_queue = asyncio.Queue()
    stt = DeepgramSTT(stt_output_queue)

    async def print_output():
        while True:
            item = await stt_output_queue.get()
            logging.info(f"STT Output: {item}")
            stt_output_queue.task_done()

    print_task = asyncio.create_task(print_output())

    await stt.start()

    # Give connection a moment to open before sending data
    await asyncio.sleep(2.0)

    # Simulate sending audio chunks (replace with audio source)
    # Example: Send dummy data for a few seconds
    logging.info("Simulating sending audio...")
    start_time = asyncio.get_event_loop().time()
    while asyncio.get_event_loop().time() < start_time + 10:
         # In real use, get audio_chunk from audio.py
         dummy_chunk = b'\x00\x00' * 960 # Simulate 20ms of silence (16-bit mono @ 48kHz)
         await stt.send_audio(dummy_chunk)
         await asyncio.sleep(0.020) # Wait 20ms

    logging.info("Stopping simulation...")
    await stt.stop()
    print_task.cancel()
    try:
        await print_task
    except asyncio.CancelledError:
         pass
    logging.info("Finished STT test.")

if __name__ == "__main__":
    if not API_KEY:
        logging.error("DEEPGRAM_API_KEY environment variable not set.")
    else:
        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            logging.info("STT test interrupted.") 