import time
import logging
from queue import Queue
from threading import current_thread
from typing import Dict, Any

# --------------------------------------------------------------------
# IMPORT MODULES
# --------------------------------------------------------------------
# The rooms module is necessary to print the room ID in the prompt
import main_data

logger = logging.getLogger(__name__)


def input_loop(result_queue: Queue):
    """
    Thread responsible for reading user input.
    """
    current_thread().name = "Input"
    logger.info("Input thread active.")

    # Access rooms module from main_data
    rooms = main_data.rooms

    while True:
        time.sleep(0.2)
        try:
            # Signal to write (queries current room from rooms module)
            user_input = input(f"\n[{rooms.get_current_room_id()}] You: ").strip()

            if user_input:
                # Immediately put input into result_queue for processing
                result_queue.put({"type": "user_input", "content": user_input})

        except (EOFError, KeyboardInterrupt):
            # Shutdown on CTRL+D or CTRL+C
            result_queue.put({"type": "exit"})
            break