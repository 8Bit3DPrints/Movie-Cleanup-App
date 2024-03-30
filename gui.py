import tkinter as tk
from tkinter import filedialog, messagebox
import threading
import json
from movie_cleanup import clean_unwanted_files, organize_files_into_folders, move_and_rename_subtitles_and_nfo, rename_movie_folders

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
        # Directory selection
        tk.Label(self.master, text="Movie Directory:").grid(row=0, column=0, sticky="w")
        self.movie_directory_var = tk.StringVar(value=self.config.get("movies_directory", ""))
        tk.Entry(self.master, textvariable=self.movie_directory_var, width=50).grid(row=0, column=1)
        tk.Button(self.master, text="Browse", command=self.select_movie_directory).grid(row=0, column=2)

        # Configurable lists (extensions, etc.)
        tk.Label(self.master, text="Unwanted Extensions (comma-separated):").grid(row=1, column=0, sticky="w")
        self.unwanted_ext_var = tk.StringVar(value=",".join(self.config.get("unwanted_extensions", [])))
        tk.Entry(self.master, textvariable=self.unwanted_ext_var, width=50).grid(row=1, column=1, columnspan=2)

        # Save configuration button
        tk.Button(self.master, text="Save Configuration", command=self.save_configuration).grid(row=3, column=1)

        # Start button
        self.start_button = tk.Button(self.master, text="Start Cleanup", command=self.run_script)
        self.start_button.grid(row=4, column=1)

        # Logging messages display
        self.log_text = tk.Text(self.master, height=10, width=75)
        self.log_text.grid(row=5, column=0, columnspan=3)
        self.log_text.insert(tk.END, "Logging messages will appear here...\n")

    def select_movie_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.movie_directory_var.set(directory)

    def save_configuration(self):
        self.config["movies_directory"] = self.movie_directory_var.get()
        self.config["unwanted_extensions"] = [ext.strip() for ext in self.unwanted_ext_var.get().split(",") if ext.strip()]
        # Add saving for other config items here

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
                move_and_rename_subtitles_and_nfo(self.config["movies_directory"], self.config["subtitle_folder_names"], self.config["movie_extensions"])
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

if __name__ == "__main__":
    root = tk.Tk()
    app = MovieCleanupGUI(root, 'config.json')
    root.mainloop()