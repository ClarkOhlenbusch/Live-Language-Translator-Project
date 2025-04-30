import asyncio
import sounddevice as sd
import numpy as np
import logging
import functools # Import functools

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Configuration ---
SAMPLE_RATE = 48000  # Hz
# 20ms chunks at 48kHz --> 0.020 * 48000 = 960 frames
CHUNK_SIZE = 960
CHANNELS = 1 # Mono
DTYPE = 'float32' # Data type for audio samples

# Device names (adjust if necessary based on your system's device list)
# Use 'python -m sounddevice' in terminal to list devices
LOOPBACK_DEVICE_NAME = 'CABLE Output (VB-Audio Virtual Cable)' # Name of the VB-Audio loopback device *recording* end
# Leave MIC_DEVICE_NAME as None to use the default input device
MIC_DEVICE_NAME = 'Microphone Array (Realtek(R) Audio)'
TARGET_HOSTAPI = 'WASAPI' # Windows specific low-latency API

# Queues for inter-coroutine communication
loopback_queue = asyncio.Queue()
mic_queue = asyncio.Queue()

# --- Device Discovery ---

def find_device_index(device_name_substring: str | None, hostapi_name: str, is_input: bool) -> int | None:
    """Finds the index of an audio device based on substring match and host API."""
    try:
        devices = sd.query_devices()
        hostapis = sd.query_hostapis()
        # Get the system default input/output device indices
        default_input_idx, default_output_idx = sd.default.device
        logging.debug(f"System default devices: Input={default_input_idx}, Output={default_output_idx}")
    except Exception as e:
        logging.error(f"Error querying audio devices: {e}")
        return None

    target_hostapi_index = -1
    for i, api in enumerate(hostapis):
        if hostapi_name.lower() in api['name'].lower():
            target_hostapi_index = i
            break

    if target_hostapi_index == -1:
        logging.warning(f"Host API '{hostapi_name}' not found.")
        return None

    matching_devices = []
    found_default_for_api = False
    for index, device in enumerate(devices):
        # Filter by host API and direction
        is_correct_hostapi = device['hostapi'] == target_hostapi_index
        is_correct_direction = (is_input and device['max_input_channels'] > 0) or \
                               (not is_input and device['max_output_channels'] > 0)

        if not (is_correct_hostapi and is_correct_direction):
            continue

        # If a specific name is given, check for substring match
        if device_name_substring:
            if device_name_substring.lower() in device['name'].lower():
                matching_devices.append(index)
                logging.debug(f"Found match by name: Index={index}, Name={device['name']}")
        # If no name is given, check if this device is the system default *for the target host API*
        # We check if the index matches the system default AND it uses the target host API
        elif index == (default_input_idx if is_input else default_output_idx):
             matching_devices.append(index)
             found_default_for_api = True
             logging.debug(f"Found system default match using target API: Index={index}, Name={device['name']}")
             # If we found the default for this API, we can stop searching for the default case.
             # Note: A named search might still find other devices.
             # break # Don't break, allows named search to find others if needed, though unlikely mix scenario.

    # If searching for default (no name) AND we didn't find the system default using the target API
    if not device_name_substring and not found_default_for_api:
        direction = "input" if is_input else "output"
        system_default_idx = default_input_idx if is_input else default_output_idx
        try:
            system_default_name = devices[system_default_idx]['name']
            system_default_api_idx = devices[system_default_idx]['hostapi']
            system_default_api_name = hostapis[system_default_api_idx]['name']
            logging.warning(
                f"System default {direction} device (Index: {system_default_idx}, Name: '{system_default_name}', API: '{system_default_api_name}') "
                f"does not use the target Host API '{hostapi_name}'. Cannot reliably determine the default device for '{hostapi_name}'. "
                f"Please specify the device name explicitly in the configuration (e.g., MIC_DEVICE_NAME)."
            )
        except IndexError:
             logging.warning(f"Could not retrieve info for system default {direction} device index {system_default_idx}.")

        # Attempt to find *any* device matching the host API as a fallback? Risky. Let's return None.
        return None

    if not matching_devices:
        name_str = f"'{device_name_substring}' " if device_name_substring else "default "
        direction = "input" if is_input else "output"
        logging.warning(f"No {direction} device found for {name_str}with Host API '{hostapi_name}'.")
        return None
    elif len(matching_devices) > 1 and device_name_substring: # Warn if multiple matches for a specific name
        logging.warning(f"Multiple devices found for '{device_name_substring}': {matching_devices}. Using first one: {matching_devices[0]}")
    elif len(matching_devices) > 1 and not device_name_substring: # Warn if multiple defaults found (shouldn't happen?)
         logging.warning(f"Multiple default devices found for Host API '{hostapi_name}': {matching_devices}. Using first one: {matching_devices[0]}")


    return matching_devices[0]

# --- Audio Callbacks ---

def loopback_callback(indata, frames, time, status, *, loop, queue):
    """This is called (from a separate thread) for each audio block from the loopback device."""
    if status:
        logging.warning(f"Loopback stream status: {status}")
    # Schedule the queue put operation on the main event loop
    future = asyncio.run_coroutine_threadsafe(queue.put(indata.copy()), loop)
    # Optional: Add error handling for the future if needed
    # try:
    #     future.result(timeout=1) # Wait briefly for acknowledgement/exception
    # except Exception as e:
    #     logging.error(f"Error putting loopback data in queue: {e}")

def mic_callback(indata, frames, time, status, *, loop, queue):
    """This is called (from a separate thread) for each audio block from the microphone."""
    if status:
        logging.warning(f"Mic stream status: {status}")
    # Schedule the queue put operation on the main event loop
    future = asyncio.run_coroutine_threadsafe(queue.put(indata.copy()), loop)
    # Optional: Error handling
    # try:
    #     future.result(timeout=1)
    # except Exception as e:
    #     logging.error(f"Error putting mic data in queue: {e}")


# --- Main Capture Function ---

async def capture_audio(audio_queue: asyncio.Queue):
    """Asynchronously captures audio from loopback and mic, putting loopback chunks onto audio_queue."""
    # Get the main event loop *before* starting threads
    main_loop = asyncio.get_running_loop()

    loopback_index = find_device_index(LOOPBACK_DEVICE_NAME, TARGET_HOSTAPI, is_input=True)
    mic_index = find_device_index(MIC_DEVICE_NAME, TARGET_HOSTAPI, is_input=True)

    if loopback_index is None:
        logging.error(f"Could not find loopback device: {LOOPBACK_DEVICE_NAME}")
        # Consider raising an exception instead of just returning
        # raise RuntimeError(f"Loopback device not found: {LOOPBACK_DEVICE_NAME}")
        return
    if mic_index is None:
        logging.warning(f"Could not find microphone device: {MIC_DEVICE_NAME or 'Default'}. Proceeding with loopback only.")
        # Don't return, allow loopback to continue if mic fails
        # return

    logging.info(f"Using Loopback Device Index: {loopback_index} ({sd.query_devices()[loopback_index]['name']})")
    if mic_index is not None:
        logging.info(f"Using Mic Device Index: {mic_index} ({sd.query_devices()[mic_index]['name']})")

    loopback_stream = None
    mic_stream = None
    # Use temporary internal queues for the callbacks
    _loopback_q = asyncio.Queue()
    _mic_q = asyncio.Queue() 

    try:
        # Create partial functions for callbacks with the loop and *internal* queues
        partial_loopback_callback = functools.partial(loopback_callback, loop=main_loop, queue=_loopback_q)
        if mic_index is not None:
            partial_mic_callback = functools.partial(mic_callback, loop=main_loop, queue=_mic_q)

        loopback_stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            blocksize=CHUNK_SIZE,
            device=loopback_index,
            channels=CHANNELS,
            dtype=DTYPE,
            callback=partial_loopback_callback,
        )
        if mic_index is not None:
            mic_stream = sd.InputStream(
                samplerate=SAMPLE_RATE,
                blocksize=CHUNK_SIZE,
                device=mic_index,
                channels=CHANNELS,
                dtype=DTYPE,
                callback=partial_mic_callback,
            )

        logging.info("Starting audio streams...")
        loopback_stream.start()
        if mic_stream: 
            mic_stream.start()

        while True:
            # Get chunks from internal queues
            try:
                # Prioritize loopback for now
                loopback_chunk = await asyncio.wait_for(_loopback_q.get(), timeout=5.0)
                # TODO: Decide how/if to handle mic_chunk in the future (mix, separate queue?)
                # if mic_stream:
                #     mic_chunk = await asyncio.wait_for(_mic_q.get(), timeout=5.0)
                # else:
                #     mic_chunk = None

            except asyncio.TimeoutError:
                logging.warning("Timeout waiting for audio data from internal queue.")
                continue 

            # Put the loopback chunk onto the queue provided by main.py
            if loopback_chunk is not None and loopback_chunk.size > 0:
                # Convert to bytes before putting on the queue, as expected by stt.py
                audio_int16 = (loopback_chunk * 32767).astype(np.int16)
                audio_bytes = audio_int16.tobytes()
                await audio_queue.put(audio_bytes)
            
            # Mark task as done for the internal queues
            _loopback_q.task_done()
            # if mic_stream: 
            #     _mic_q.task_done()

    except asyncio.CancelledError:
        logging.info("Audio capture task cancelled.") # Expected on shutdown
    except Exception as e:
        logging.error(f"Error during audio capture: {e}")
    finally:
        logging.info("Stopping audio streams...")
        if loopback_stream:
            loopback_stream.stop()
            loopback_stream.close()
        if mic_stream:
            mic_stream.stop()
            mic_stream.close()
        logging.info("Audio streams stopped.")


# --- Example Usage (for testing this module directly) ---
async def main():
    logging.info("Starting audio capture test...")
    async for loopback_data, mic_data in capture_audio():
        # In a real application, these chunks would be processed (e.g., sent to STT)
        logging.info(f"Received chunk: Loopback shape={loopback_data.shape}, Mic shape={mic_data.shape}")
        # Add a condition to stop after a few seconds for testing
        # For example, stop after 5 seconds:
        # if asyncio.get_event_loop().time() > start_time + 5:
        #     break

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Capture test interrupted.") 