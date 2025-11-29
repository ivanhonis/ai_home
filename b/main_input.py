import time
import logging
from queue import Queue
from threading import current_thread
from typing import Dict, Any

# --------------------------------------------------------------------
# IMPORT MODULES
# --------------------------------------------------------------------
# UPDATED: rooms -> modes logic via main_data
import main_data

logger = logging.getLogger(__name__)


def input_loop(result_queue: Queue):
    """
    Thread responsible for reading user input.
    """
    current_thread().name = "Input"
    logger.info("Input thread active.")

    # Access modes module from main_data (was rooms)
    modes = main_data.modes

    while True:
        time.sleep(0.2)
        try:
            # Signal to write (queries current mode from modes module)
            # UPDATED: Prompt now shows [mode_id]
            user_input = input(f"\n[{modes.get_current_mode_id()}] You: ").strip()

            if user_input:
                # Immediately put input into result_queue for processing
                result_queue.put({"type": "user_input", "content": user_input})

        except (EOFError, KeyboardInterrupt):
            # Shutdown on CTRL+D or CTRL+C
            result_queue.put({"type": "exit"})
            break