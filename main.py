import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import os
import yt_dlp

class YouTubeDownloader:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Video Downloader")
        self.root.geometry("600x550")  # Increased height for new audio options
        self.root.resizable(False, False)

        self.available_formats = [
            ("Best Quality", "bestvideo+bestaudio/best"),
            ("1080p", "bestvideo[height<=1080]+bestaudio/best[height<=1080]"),
            ("720p", "bestvideo[height<=720]+bestaudio/best[height<=720]"),
            ("480p", "bestvideo[height<=480]+bestaudio/best[height<=480]"),
            ("360p", "bestvideo[height<=360]+bestaudio/best[height<=360]"),
        ]

        self.audio_formats = [
            ("MP3 (Best Quality)", "mp3", "best"),
            ("MP3 (320 kbps)", "mp3", "320"),
            ("MP3 (256 kbps)", "mp3", "256"),
            ("MP3 (192 kbps)", "mp3", "192"),
            ("MP3 (128 kbps)", "mp3", "128"),
            ("M4A (AAC)", "m4a", "best"),
            ("OPUS", "opus", "best"),
            ("WAV", "wav", "best"),
        ]

        self.default_download_path = os.path.join(os.path.expanduser("~"), "Downloads")
        self.create_widgets()

    def create_widgets(self):
        # URL Entry
        ttk.Label(self.root, text="YouTube URL:").pack(pady=5)
        self.url_entry = ttk.Entry(self.root, width=70)
        self.url_entry.pack(pady=5)

        # Notebook for Video/Audio tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(pady=10, fill='x', padx=10)

        # Video Tab
        self.video_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.video_tab, text="Video")

        # Resolution Options in Video Tab
        ttk.Label(self.video_tab, text="Select Video Quality:").pack(pady=5)
        self.resolution_var = tk.StringVar(value=self.available_formats[0][0])
        self.resolution_dropdown = ttk.Combobox(
            self.video_tab,
            textvariable=self.resolution_var,
            values=[opt[0] for opt in self.available_formats],
            state="readonly",
            width=65
        )
        self.resolution_dropdown.pack(pady=5)

        # Audio Tab
        self.audio_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.audio_tab, text="Audio Only")

        # Audio Format Options in Audio Tab
        ttk.Label(self.audio_tab, text="Select Audio Format:").pack(pady=5)
        self.audio_format_var = tk.StringVar(value=self.audio_formats[0][0])
        self.audio_format_dropdown = ttk.Combobox(
            self.audio_tab,
            textvariable=self.audio_format_var,
            values=[opt[0] for opt in self.audio_formats],
            state="readonly",
            width=65
        )
        self.audio_format_dropdown.pack(pady=5)

        # Download Path (common for both tabs)
        ttk.Label(self.root, text="Download Path:").pack(pady=5)
        path_frame = ttk.Frame(self.root)
        path_frame.pack(pady=5)
        self.path_entry = ttk.Entry(path_frame, width=50)
        self.path_entry.insert(0, self.default_download_path)
        self.path_entry.pack(side=tk.LEFT, padx=5)
        browse_button = ttk.Button(path_frame, text="Browse", command=self.browse_path)
        browse_button.pack(side=tk.LEFT)

        # Download Button
        download_button = ttk.Button(self.root, text="Download", command=self.start_download)
        download_button.pack(pady=20)

        # Status Label
        self.status_label = ttk.Label(self.root, text="", font=("Segoe UI", 10))
        self.status_label.pack(pady=5)

    def browse_path(self):
        path = filedialog.askdirectory()
        if path:
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, path)

    def start_download(self):
        url = self.url_entry.get().strip()
        path = self.path_entry.get().strip()

        if not url:
            messagebox.showerror("Error", "Please enter a YouTube URL.")
            return
        if not path:
            messagebox.showerror("Error", "Please select a download path.")
            return

        current_tab = self.notebook.tab(self.notebook.select(), "text")
        
        if current_tab == "Video":
            resolution_label = self.resolution_var.get()
            format_string = dict(self.available_formats)[resolution_label]
            is_audio_only = False
        else:  # Audio tab
            audio_format_label = self.audio_format_var.get()
            selected_format = next((f for f in self.audio_formats if f[0] == audio_format_label), None)
            if selected_format:
                format_string = "bestaudio/best"
                is_audio_only = True
                audio_format = selected_format[1]
                audio_quality = selected_format[2]
            else:
                messagebox.showerror("Error", "Invalid audio format selected.")
                return

        threading.Thread(
            target=self.download_video, 
            args=(url, path, format_string, is_audio_only, audio_format if is_audio_only else None, audio_quality if is_audio_only else None),
            daemon=True
        ).start()

    def download_video(self, url, path, format_string, is_audio_only, audio_format=None, audio_quality=None):
        self.update_status("Starting download...")

        ydl_opts = {
            'format': format_string,
            'outtmpl': os.path.join(path, '%(title)s.%(ext)s'),
            'ffmpeg_location': r'C:\ffmpeg\bin',  # Update if not on Windows or FFmpeg is in PATH
            'quiet': True,
            'no_warnings': True,
            'progress_hooks': [self.ydl_hook],
        }

        if is_audio_only and audio_format:
            ydl_opts.update({
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': audio_format,
                    'preferredquality': audio_quality,
                }],
                'extractaudio': True,  # Only keep the audio
            })
        else:
            ydl_opts.update({
                'merge_output_format': 'mp4',
                'postprocessor_args': [
                    '-c:a', 'aac',
                    '-b:a', '192k'
                ],
            })

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            self.update_status("Download completed successfully.")
            messagebox.showinfo("Success", "Download completed successfully.")
        except Exception as e:
            self.update_status("Download failed.")
            messagebox.showerror("Error", f"An error occurred: {str(e)}")

    def ydl_hook(self, d):
        if d['status'] == 'downloading':
            percent = d.get('_percent_str', '').strip().replace('%', '')
            speed = d.get('_speed_str', '').strip()
            try:
                percent_int = int(float(percent))
                self.update_status(f"Downloading... {percent_int}% at {speed}")
            except ValueError:
                self.update_status(f"Downloading... at {speed}")
        elif d['status'] == 'finished':
            self.update_status("Download finished, now post-processing...")

    def update_status(self, message):
        self.status_label.config(text=message)

if __name__ == "__main__":
    root = tk.Tk()
    app = YouTubeDownloader(root)
    root.mainloop()