import logging
import os
import shutil
import traceback

logger = logging.getLogger(__name__)

def clear_folder(folder: str) -> bool:

    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception:
            logger.error("Failed to delete: ", traceback.format_exc())

    return True
