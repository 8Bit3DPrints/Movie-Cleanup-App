import os
import shutil
import logging
import glob
import time
import re
from functools import wraps

# Retry decorator for robust error handling
def retry(exceptions, tries=4, delay=1, backoff=2):
    def decorator_retry(func):
        @wraps(func)
        def f_retry(*args, **kwargs):
            _tries, _delay = tries, delay
            while _tries > 1:
                try:
                    return func(*args, **kwargs)                
                except exceptions as e:
                    msg = f"{str(e)}, Retrying in {_delay} seconds..."
                    logging.warning(msg)
                    time.sleep(_delay)
                    _tries -= 1
                    _delay *= backoff
            return func(*args, **kwargs)
        return f_retry
    return decorator_retry

def is_excluded_subtitle(filename):
    """
    Checks if a filename matches patterns known to be non-English subtitles,
    which might otherwise be misidentified due to containing English identifiers.
    This function is adjusted to explicitly catch '3_French.srt' and similar patterns.
    """
    excluded_patterns = [
        r"\bFrench\b",
        r"\bfr\b",  # Common abbreviation for French
        # Add other non-English language patterns or specific cases as necessary
        r"3_French",  # Specific case for '3_French.srt'
    ]

    for pattern in excluded_patterns:
        if re.search(pattern, filename, re.IGNORECASE):
            return True
    return False


def is_english_subtitle(filename):
    """
    Check if a filename matches English subtitle criteria more strictly.
    This function now also calls is_excluded_subtitle to filter out known non-English patterns.
    """
    if is_excluded_subtitle(filename):
        return False

    english_patterns = [
        r"\beng\b", r"\benglish\b",
        r"_eng\b", r"_english\b",
        r"\beng_", r"\benglish_",
    ]

    for pattern in english_patterns:
        if re.search(pattern, filename, re.IGNORECASE):
            return True
    return False

@retry((Exception), tries=4, delay=1, backoff=2)
def clean_unwanted_files(directory, extensions):
    if not os.path.exists(directory):
        logging.error(f"The path {directory} is not a valid path.")
        return

    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(extensions):
                try:
                    os.remove(os.path.join(root, file))
                    logging.info(f"Deleted {os.path.join(root, file)}")
                except PermissionError as e:
                    logging.warning(f"Permission denied when trying to delete {os.path.join(root, file)}: {e}")
                except FileNotFoundError as e:
                    logging.warning(f"File not found when trying to delete {os.path.join(root, file)}: {e}")
                except Exception as e:
                    logging.error(f"Error deleting {os.path.join(root, file)}: {e}")

@retry((Exception), tries=4, delay=1, backoff=2)
def organize_files_into_folders(directory):
    if not os.path.exists(directory):
        logging.error(f"The path {directory} is not a valid path.")
        return

    for item in os.listdir(directory):
        if item.startswith('.'):
            continue
        if os.path.isfile(os.path.join(directory, item)):
            folder_name = os.path.splitext(item)[0]
            folder_path = os.path.join(directory, folder_name)
            try:
                if not os.path.exists(folder_path):
                    os.makedirs(folder_path)
                    logging.info(f"Created folder: {folder_path}")
                shutil.move(os.path.join(directory, item), folder_path)
                logging.info(f"Moved: {item} to {folder_path}")
            except Exception as e:
                logging.error(f"Error organizing {item} into folders: {e}")

@retry((Exception), tries=4, delay=1, backoff=2)
def move_and_rename_subtitles_and_nfo(config):
    directory = config["movies_directory"]
    subtitle_folder_names = config["subtitle_folder_names"]
    movie_extensions = config["movie_extensions"]
    english_identifiers = config.get("english_identifiers", ["eng", "english", "en"])

    if not os.path.exists(directory):
        logging.error(f"The path {directory} is not a valid path.")
        return

    for root, dirs, files in os.walk(directory, topdown=False):
        movie_files = [f for f in files if os.path.splitext(f)[1] in movie_extensions]
        subtitle_files = [f for f in files if f.endswith('.srt')]

        # Check for exact subtitle matches first and remove all non-matching subtitles
        for movie_file in movie_files:
            movie_base_name = os.path.splitext(movie_file)[0]
            exact_match_subtitle_name = f"{movie_base_name}.srt"
            exact_match_subtitle = None

            # Identify the exact match subtitle if it exists
            for sub_file in subtitle_files:
                if sub_file == exact_match_subtitle_name:
                    exact_match_subtitle = sub_file
                    break

            # If there's an exact match, delete all other subtitle files
            if exact_match_subtitle:
                for sub_file in subtitle_files:
                    if sub_file != exact_match_subtitle:
                        sub_file_path = os.path.join(root, sub_file)
                        os.remove(sub_file_path)
                        logging.info(f"Deleted non-matching subtitle: {sub_file}")
                # Continue to the next movie file after handling subtitles for this one
                continue

            # For movies without an exact matching subtitle, process other subtitles
            for dir in dirs:
                if dir in subtitle_folder_names:
                    sub_folder_path = os.path.join(root, dir)
                    try:
                        for filename in os.listdir(sub_folder_path):
                            source = os.path.join(sub_folder_path, filename)
                            if filename.endswith('.srt'):
                                # Move only English subtitles
                                if is_english_subtitle(filename):
                                    destination = os.path.join(root, filename)
                                    shutil.move(source, destination)
                                    logging.info(f"Moved: {source} to {destination}")
                                else:
                                    # Delete non-English subtitles
                                    os.remove(source)
                                    logging.info(f"Deleted non-English subtitle: {source}")
                        shutil.rmtree(sub_folder_path)
                        logging.info(f"Deleted folder: {sub_folder_path}")
                    except Exception as e:
                        logging.error(f"Error moving or deleting subtitle files in {sub_folder_path}: {e}")

            # Additional logic for renaming .srt and .nfo files
            for file_to_rename in files:
                if file_to_rename.endswith('.srt') or file_to_rename.endswith('.nfo'):
                    new_name = f"{movie_base_name}{os.path.splitext(file_to_rename)[1]}"
                    old_file_path = os.path.join(root, file_to_rename)
                    new_file_path = os.path.join(root, new_name)
                    try:
                        if not os.path.exists(new_file_path):
                            os.rename(old_file_path, new_file_path)
                            logging.info(f"Renamed: {file_to_rename} to {new_name}")
                        else:
                            logging.warning(f"Skipped: {file_to_rename} already matches the movie name or target name exists.")
                    except Exception as e:
                        logging.error(f"Error renaming {file_to_rename} to {new_name}: {e}")

@retry((Exception), tries=4, delay=1, backoff=2)
def rename_movie_folders(directory, movie_extensions):
    if not os.path.exists(directory):
        logging.error(f"The path {directory} is not a valid path.")
        return

    for root, dirs, _ in os.walk(directory, topdown=False):
        for dir in dirs:
            folder_path = os.path.join(root, dir)
            for file in os.listdir(folder_path):
                file_extension = os.path.splitext(file)[1]
                if file_extension in movie_extensions:
                    movie_base_name = os.path.splitext(file)[0]
                    new_folder_path = os.path.join(root, movie_base_name)
                    try:
                        if folder_path != new_folder_path:
                            os.rename(folder_path, new_folder_path)
                            logging.info(f"Renamed folder: {dir} to {movie_base_name}")
                    except Exception as e:
                        logging.error(f"Error renaming folder {dir} to {movie_base_name}: {e}")

def manage_log_files(logs_dir, max_files=10):
    log_files = sorted(glob.glob(os.path.join(logs_dir, "movie_cleanup_*.log")), key=os.path.getmtime, reverse=True)
    for file_to_delete in log_files[max_files:]:
        os.remove(file_to_delete)
        logging.info(f"Deleted old log file: {file_to_delete}")
