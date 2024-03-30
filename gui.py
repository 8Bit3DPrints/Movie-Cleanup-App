import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import json
from movie_cleanup import (clean_unwanted_files, organize_files_into_folders, 
                           process_subtitles, rename_subtitles_and_nfo, 
                           rename_movie_folders)

class MovieCleanupGUI:
    def __init__(self, master, config_path):
        self.master = master
        self.master.title("Movie Cleanup Tool")
        self.config_path = config_path
        self.config = self.load_config()

        self.setup_gui()

    def load_config(self):
        with open(self.config_path, 'r') as file:
            return json.load(file)

    def save_config(self):
        with open(self.config_path, 'w') as file:
            json.dump(self.config, file, indent=4)

    def setup_gui(self):
        control_frame = ttk.Frame(self.master)
        control_frame.pack(padx=10, pady=10, fill=tk.X)

        log_frame = ttk.Frame(self.master)
        log_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # Directory selection
        ttk.Label(control_frame, text="Movie Directory:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.movie_directory_var = tk.StringVar(value=self.config.get("movies_directory", ""))
        ttk.Entry(control_frame, textvariable=self.movie_directory_var, width=50).grid(row=0, column=1, padx=5, pady=2)
        ttk.Button(control_frame, text="Browse", command=self.select_movie_directory).grid(row=0, column=2, padx=5, pady=2)

        # Configurable lists (extensions, etc.)
        ttk.Label(control_frame, text="Unwanted Extensions (comma-separated):").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.unwanted_ext_var = tk.StringVar(value=",".join(self.config.get("unwanted_extensions", [])))
        ttk.Entry(control_frame, textvariable=self.unwanted_ext_var, width=50).grid(row=1, column=1, columnspan=2, padx=5, pady=2)

        # Action buttons
        ttk.Button(control_frame, text="Save Configuration", command=self.save_configuration).grid(row=2, column=0, columnspan=3, padx=5, pady=5)
        ttk.Button(control_frame, text="Start Cleanup", command=self.run_script).grid(row=3, column=0, columnspan=3, padx=5, pady=2)
        ttk.Button(control_frame, text="Clean Unwanted Files", command=self.start_clean_unwanted_files).grid(row=4, column=0, columnspan=3, padx=5, pady=2)
        ttk.Button(control_frame, text="Organize Files into Folders", command=self.start_organize_files_into_folders).grid(row=5, column=0, columnspan=3, padx=5, pady=2)
        ttk.Button(control_frame, text="Process Subtitles", command=self.start_process_subtitles).grid(row=6, column=0, columnspan=3, padx=5, pady=2)
        ttk.Button(control_frame, text="Rename Subtitles and NFO", command=self.start_rename_subtitles_and_nfo).grid(row=7, column=0, columnspan=3, padx=5, pady=2)
        ttk.Button(control_frame, text="Rename Movie Folders", command=self.start_rename_movie_folders).grid(row=8, column=0, columnspan=3, padx=5, pady=2)
        
        # Log messages display
        self.log_text = tk.Text(log_frame, height=10, width=75)
        self.log_text.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)
        self.log_text.insert(tk.END, "Logging messages will appear here...\n")

    def select_movie_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.movie_directory_var.set(directory)

    def save_configuration(self):
        self.config["movies_directory"] = self.movie_directory_var.get()
        self.config["unwanted_extensions"] = [ext.strip() for ext in self.unwanted_ext_var.get().split(",") if ext.strip()]
        self.save_config()
        messagebox.showinfo("Configuration", "Configuration saved successfully.")

    def append_log_message(self, message):
        # This method should also be made thread-safe if called from another thread
        def callback():
            self.log_text.insert(tk.END, message + "\n")
            self.log_text.see(tk.END)
        self.master.after(0, callback)

    def run_script(self):
        # Disable the start button to prevent multiple clicks
        self.start_button.config(state="disabled")
        self.append_log_message("Starting cleanup...")

        # Define the target function for the thread
        def target():
            try:
                # Update config with GUI inputs
                self.config["movies_directory"] = self.movie_directory_var.get()
                # Ensure you are using self.config for script operations
                # Note: Directly using the methods might not update the GUI with logs. You might need a custom logging handler.
                organize_files_into_folders(self.config["movies_directory"])
                clean_unwanted_files(self.config["movies_directory"], tuple(self.config["unwanted_extensions"]))
                rename_movie_folders(self.config["movies_directory"], self.config["movie_extensions"])

                # Safely updating the GUI from another thread
                self.append_log_message("Cleanup completed successfully.")
            except Exception as e:
                    self.append_log_message(f"An error occurred: {str(e)}")
            finally:
                    # Safely re-enable the start button
                    self.master.after(0, lambda: self.start_button.config(state="normal"))

        # Create a Thread to run the script logic
        script_thread = threading.Thread(target=target)
        # Start the thread
        script_thread.start()

    def start_clean_unwanted_files(self):
        """Start cleaning unwanted files in a separate thread."""
        threading.Thread(target=self.clean_unwanted_files_task, daemon=True).start()

    def start_organize_files_into_folders(self):
        """Start organizing files into folders in a separate thread."""
        threading.Thread(target=self.organize_files_into_folders_task, daemon=True).start()

    def clean_unwanted_files_task(self):
        """Task to clean unwanted files."""
        self.append_log_message("Cleaning unwanted files...")
        try:
            clean_unwanted_files(self.config["movies_directory"], tuple(self.config["unwanted_extensions"]))
            self.append_log_message("Finished cleaning unwanted files.")
        except Exception as e:
            self.append_log_message(f"An error occurred: {str(e)}")

    def organize_files_into_folders_task(self):
        """Task to organize files into folders."""
        self.append_log_message("Organizing files into folders...")
        try:
            organize_files_into_folders(self.config["movies_directory"])
            self.append_log_message("Finished organizing files into folders.")
        except Exception as e:
            self.append_log_message(f"An error occurred: {str(e)}")    

    def start_process_subtitles(self):
        """Start processing subtitles in a separate thread."""
        threading.Thread(target=self.process_subtitles_task, daemon=True).start()

    def start_rename_subtitles_and_nfo(self):
        """Start renaming subtitles and NFO files in a separate thread."""
        threading.Thread(target=self.rename_subtitles_and_nfo_task, daemon=True).start()

    def process_subtitles_task(self):
        """Task to process subtitles."""
        self.append_log_message("Processing subtitles...")
        try:
            process_subtitles(self.config)  # Assuming this function exists in movie_cleanup module
            self.append_log_message("Finished processing subtitles.")
        except Exception as e:
            self.append_log_message(f"An error occurred while processing subtitles: {str(e)}")

    def rename_subtitles_and_nfo_task(self):
        """Task to rename subtitles and NFO files."""
        self.append_log_message("Renaming subtitles and NFO files...")
        try:
            rename_subtitles_and_nfo(self.config)  # Assuming this function exists in movie_cleanup module
            self.append_log_message("Finished renaming subtitles and NFO files.")
        except Exception as e:
            self.append_log_message(f"An error occurred while renaming subtitles and NFO files: {str(e)}")

    def start_rename_movie_folders(self):
        """Start renaming movie folders in a separate thread."""
        threading.Thread(target=self.rename_movie_folders_task, daemon=True).start()

    def rename_movie_folders_task(self):
        """Task to rename movie folders."""
        self.append_log_message("Renaming movie folders...")
        try:
            rename_movie_folders(self.config["movies_directory"], tuple(self.config["movie_extensions"]))
            self.append_log_message("Finished renaming movie folders.")
        except Exception as e:
            self.append_log_message(f"An error occurred while renaming movie folders: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = MovieCleanupGUI(root, 'config.json')
    root.mainloop()
