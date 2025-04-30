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
    verbose=logging.DEBUG,
    # Add keepalive option if needed later for long pauses
    # options={"keepalive": "true"}
)

# Deepgram connection options (Updated for Italian)
options: LiveOptions = LiveOptions(
    model="nova-2",       # Use Nova-2 model
    language="it",        # Set language to Italian
    smart_format=True,    # Enable smart formatting
    encoding="linear16",
    sample_rate=48000,
    channels=1,
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
        logging.info("DeepgramSTT initialized.")

    async def start(self):
        """Starts the Deepgram connection and event handling task."""
        # Register handlers before starting the task
        self._register_handlers()
        if self._task is None:
            self._task = asyncio.create_task(self._run())
            logging.info("DeepgramSTT task started.")
        else:
            logging.warning("DeepgramSTT task already running.")

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
        else:
            logging.info("DeepgramSTT task not running.")
        # Disconnect is handled in the _run loop's finally block or on error

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
        open_data = kwargs.get('open')
        logging.info(f"Deepgram connection opened. Data: {open_data}, Args: {args}, Kwargs: {kwargs}")
        self._is_connected = True # Set connected flag

    async def _on_message(self, *args, **kwargs):
        result = kwargs.get('result')
        if not result:
            logging.warning(f"_on_message called but no 'result' in kwargs. Args: {args}, Kwargs: {kwargs}")
            return

        # logging.debug(f"_on_message received. Result type: {type(result)}, Kwargs: {kwargs}")
        transcript = result.channel.alternatives[0].transcript
        if transcript:
            await self.output_queue.put({
                "type": "transcript",
                "is_final": result.is_final,
                "transcript": transcript,
                "confidence": result.channel.alternatives[0].confidence,
            })

    async def _on_metadata(self, *args, **kwargs):
        metadata = kwargs.get('metadata')
        logging.debug(f"Received metadata. Data: {metadata}, Args: {args}, Kwargs: {kwargs}")

    async def _on_speech_started(self, *args, **kwargs):
        speech_started = kwargs.get('speech_started')
        logging.debug(f"Speech started event. Data: {speech_started}, Args: {args}, Kwargs: {kwargs}")

    async def _on_utterance_end(self, *args, **kwargs):
        utterance_end = kwargs.get('utterance_end')
        logging.debug(f"Utterance end event. Data: {utterance_end}, Args: {args}, Kwargs: {kwargs}")

    async def _on_error(self, *args, **kwargs):
        error = kwargs.get('error')
        logging.error(f"Deepgram error event. Error: {error}, Args: {args}, Kwargs: {kwargs}")
        self._is_connected = False # Set connected flag to false

    async def _on_close(self, *args, **kwargs):
        close_data = kwargs.get('close')
        logging.info(f"Deepgram connection closed event. Data: {close_data}, Args: {args}, Kwargs: {kwargs}")
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