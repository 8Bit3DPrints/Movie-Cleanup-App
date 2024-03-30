import os
import shutil
import logging
import glob
import time
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
def move_and_rename_subtitles_and_nfo(directory, subtitle_folder_names, movie_extensions):
    if not os.path.exists(directory):
        logging.error(f"The path {directory} is not a valid path.")
        return

    for root, dirs, files in os.walk(directory, topdown=False):
        for dir in dirs:
            if dir in subtitle_folder_names:
                sub_folder_path = os.path.join(root, dir)
                try:
                    for filename in os.listdir(sub_folder_path):
                        if filename.endswith('.srt'):
                            source = os.path.join(sub_folder_path, filename)
                            destination = os.path.join(root, filename)
                            shutil.move(source, destination)
                            logging.info(f"Moved: {source} to {destination}")
                    shutil.rmtree(sub_folder_path)
                    logging.info(f"Deleted folder: {sub_folder_path}")
                except Exception as e:
                    logging.error(f"Error moving or deleting subtitle files in {sub_folder_path}: {e}")

        for file in files:
            file_extension = os.path.splitext(file)[1]
            if file_extension in movie_extensions:
                movie_base_name = os.path.splitext(file)[0]
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
                                if old_file_path != new_file_path:
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
