import importlib.metadata
import logging
import os
import shutil
from datetime import datetime

logger = logging.getLogger(__name__)

def get_version() -> str:
    return importlib.metadata.version("pixivutil-server")

def clear_folder(folder: str) -> bool:
    try:
        filenames = os.listdir(folder)
    except FileNotFoundError as e:
        logger.error("Failed to clear folder '%s': folder not found (%s)", folder, e)
        return False
    except NotADirectoryError as e:
        logger.error("Failed to clear folder '%s': path is not a directory (%s)", folder, e)
        return False
    except PermissionError as e:
        logger.error("Failed to clear folder '%s': permission denied (%s)", folder, e)
        return False
    except OSError as e:
        logger.error("Failed to clear folder '%s': OS error (%s)", folder, e)
        return False

    for filename in filenames:
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except FileNotFoundError as e:
            logger.warning("Skipped deleting '%s': path no longer exists (%s)", file_path, e)
        except PermissionError as e:
            logger.error("Failed to delete '%s': permission denied (%s)", file_path, e)
        except IsADirectoryError as e:
            logger.error("Failed to delete '%s': expected file, found directory (%s)", file_path, e)
        except NotADirectoryError as e:
            logger.error("Failed to delete '%s': expected directory, found file (%s)", file_path, e)
        except OSError as e:
            logger.error("Failed to delete '%s': OS error (%s)", file_path, e)

    return True

def is_valid_date(date: str) -> bool:
    """
    Check if a date string is in the format YYYY-MM-DD.
    """
    try:
        datetime.strptime(date, "%Y-%m-%d")
        return True
    except ValueError:
        return False
