"""
GUI window for the Whisper Transcriber application.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import logging
from typing import List, Optional, Dict
import threading
import queue
import json
import time
import contextlib
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from openai import OpenAI, OpenAIError
from ..transcription import WhisperTranscriber

logger = logging.getLogger(__name__)

class TranscriptionQueue:
    """Manages the queue of files to be transcribed."""
    
    def __init__(self):
        self._queue = queue.Queue()
        self.current_file: Optional[Path] = None
        self.results: Dict[Path, str] = {}
        
    def add_file(self, file_path: Path):
        """Add a file to the queue."""
        self._queue.put(file_path)
        
    def get_next_file(self) -> Optional[Path]:
        """Get the next file from the queue."""
        try:
            self.current_file = self._queue.get_nowait()
            return self.current_file
        except queue.Empty:
            self.current_file = None
            return None
            
    def mark_complete(self, file_path: Path, result: str):
        """Mark a file as complete with its result."""
        self.results[file_path] = result
        self._queue.task_done()
        
    def empty(self) -> bool:
        """Check if the queue is empty."""
        return self._queue.empty()
        
    def qsize(self) -> int:
        """Get the current size of the queue."""
        return self._queue.qsize()
        
    def clear(self):
        """Clear all items from the queue."""
        try:
            while True:
                self._queue.get_nowait()
                self._queue.task_done()
        except queue.Empty:
            pass

class MainWindow:
    """Main application window."""
    
    def __init__(self, api_key: str, temp_dir: Path):
        """Initialize the main window."""
        self.window = tk.Tk()
        self.window.title("Whisper Transcriber")
        self.window.geometry("800x600")
        
        self.api_key = api_key
        self.temp_dir = temp_dir
        self.openai_client = OpenAI(api_key=api_key)
        self.queue = TranscriptionQueue()
        self.max_status_lines = 1000
        
        # Create temp subdirectories
        self.chunks_dir = temp_dir / "chunks"
        self.chunks_dir.mkdir(exist_ok=True)
        
        # Thread synchronization
        self.processing_lock = threading.Lock()
        self.gui_update_queue = queue.Queue()
        
        self._setup_ui()
        self._setup_bindings()
        self._cleanup_temp_files()
        self._start_gui_update_thread()
        
    def _start_gui_update_thread(self):
        """Start thread for handling GUI updates."""
        def update_gui():
            while True:
                try:
                    # Get next update with timeout
                    update_func = self.gui_update_queue.get(timeout=0.1)
                    if update_func is None:  # Shutdown signal
                        break
                    update_func()
                    self.gui_update_queue.task_done()
                except queue.Empty:
                    continue
                except Exception as e:
                    logger.error(f"Error in GUI update thread: {e}")
                    
        self.gui_update_thread = threading.Thread(target=update_gui, daemon=True)
        self.gui_update_thread.start()
        
    def _queue_gui_update(self, func):
        """Queue a GUI update to be performed in the main thread."""
        self.gui_update_queue.put(func)
        
    def _setup_ui(self):
        """Set up the user interface."""
        # File selection
        file_frame = ttk.LabelFrame(self.window, text="Files", padding=10)
        file_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.file_list = tk.Listbox(file_frame, height=6)
        self.file_list.pack(fill=tk.X, expand=True)
        
        btn_frame = ttk.Frame(file_frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(btn_frame, text="Add Files", command=self._add_files).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Remove Selected", command=self._remove_selected).pack(side=tk.LEFT)
        
        # Output directory
        out_frame = ttk.LabelFrame(self.window, text="Output", padding=10)
        out_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.output_path = tk.StringVar()
        ttk.Entry(out_frame, textvariable=self.output_path, state='readonly').pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(out_frame, text="Select", command=self._select_output).pack(side=tk.LEFT, padx=5)
        
        # Progress
        prog_frame = ttk.LabelFrame(self.window, text="Progress", padding=10)
        prog_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Overall progress
        ttk.Label(prog_frame, text="Overall:").pack(fill=tk.X)
        self.overall_progress = ttk.Progressbar(prog_frame, mode='determinate')
        self.overall_progress.pack(fill=tk.X, pady=5)
        
        # Current file progress
        ttk.Label(prog_frame, text="Current File:").pack(fill=tk.X)
        self.current_file_label = ttk.Label(prog_frame, text="")
        self.current_file_label.pack(fill=tk.X)
        self.file_progress = ttk.Progressbar(prog_frame, mode='determinate')
        self.file_progress.pack(fill=tk.X, pady=5)
        
        # Status
        self.status_text = tk.Text(prog_frame, height=8, wrap=tk.WORD)
        self.status_text.pack(fill=tk.BOTH, expand=True)
        
        # Control buttons
        ctrl_frame = ttk.Frame(self.window)
        ctrl_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.start_btn = ttk.Button(ctrl_frame, text="Start", command=self._start_processing)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.cancel_btn = ttk.Button(ctrl_frame, text="Cancel", command=self._cancel_processing, state=tk.DISABLED)
        self.cancel_btn.pack(side=tk.LEFT)
        
        # Processing state
        self.processing = False
        self.current_thread: Optional[threading.Thread] = None
        
    def _setup_bindings(self):
        """Set up event bindings."""
        self.window.protocol("WM_DELETE_WINDOW", self._on_closing)
        
    def _add_files(self):
        """Add files to the queue."""
        files = filedialog.askopenfilenames(
            title="Select Audio Files",
            filetypes=[
                ("Audio Files", "*.mp3 *.mp4 *.mpeg *.mpga *.m4a *.wav *.webm"),
                ("All Files", "*.*")
            ]
        )
        
        for file in files:
            path = Path(file)
            self.file_list.insert(tk.END, path.name)
            self.queue.add_file(path)
            
        self._update_status(f"Added {len(files)} files to queue")
        
    def _remove_selected(self):
        """Remove selected files from the list."""
        selection = self.file_list.curselection()
        for index in reversed(selection):
            self.file_list.delete(index)
            
    def _select_output(self):
        """Select output directory."""
        directory = filedialog.askdirectory(title="Select Output Directory")
        if directory:
            self.output_path.set(directory)
            
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(OpenAIError)
    )
    def _generate_filename(self, transcript: str) -> str:
        """
        Generate a filename based on the transcript content with retries.
        
        Args:
            transcript: The transcript text to analyze
            
        Returns:
            A safe filename ending in .txt
        """
        try:
            # Take only first 1000 chars for filename generation
            sample = transcript[:1000].replace('\n', ' ').strip()
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a helpful assistant that generates concise, descriptive "
                            "filenames based on transcript content. Generate a filename that's: "
                            "1) Under 50 characters 2) Uses only letters, numbers, and underscores "
                            "3) Describes the main topic/content 4) Ends with .txt"
                        )
                    },
                    {
                        "role": "user",
                        "content": f"Generate a filename for this transcript:\n\n{sample}..."
                    }
                ],
                temperature=0.7,
                max_tokens=60  # Filename should be short
            )
            
            filename = response.choices[0].message.content.strip()
            
            # Ensure filename is safe
            safe_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.")
            filename = "".join(c if c in safe_chars else "_" for c in filename)
            filename = filename.replace(" ", "_")
            
            # Ensure proper extension
            if not filename.endswith(".txt"):
                filename += ".txt"
            
            # Limit length
            if len(filename) > 50:
                base = filename[:-4]  # Remove .txt
                filename = base[:46] + ".txt"  # Leave room for .txt
            
            return filename
            
        except OpenAIError as e:
            logger.error(f"OpenAI API error generating filename: {e}")
            raise  # Let retry handle it
            
        except Exception as e:
            logger.error(f"Unexpected error generating filename: {e}")
            # Fall back to timestamp-based name
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            return f"transcript_{timestamp}.txt"
            
    def _process_queue(self):
        """Process all files in the queue."""
        try:
            total_files = self.file_list.size()
            processed_files = 0
            last_api_call = 0
            min_api_interval = 1.0  # Minimum seconds between API calls
            
            while self.processing:  # Check only processing flag
                current_file = self.queue.get_next_file()
                if current_file is None:  # No more files
                    break
                    
                try:
                    # Update GUI
                    self._queue_gui_update(lambda: self.current_file_label.config(text=current_file.name))
                    self._update_status(f"Processing {current_file.name}...")
                    
                    # Rate limiting
                    time_since_last_call = time.time() - last_api_call
                    if time_since_last_call < min_api_interval:
                        time.sleep(min_api_interval - time_since_last_call)
                    
                    # Process the file with proper resource management
                    with contextlib.ExitStack() as stack:
                        try:
                            # Create output path for this file
                            output_file = Path(self.output_path.get()) / f"temp_{int(time.time())}.txt"
                            
                            # Initialize transcriber and process file
                            with WhisperTranscriber(self.api_key, self.chunks_dir) as transcriber:
                                transcriber.transcribe_file(
                                    file_path=current_file,
                                    output_path=output_file,
                                    chunk_callback=lambda current, total: self._update_file_progress(current, total)
                                )
                                
                                # Read the transcript
                                transcript = output_file.read_text(encoding='utf-8')
                                
                                # Generate intelligent filename
                                filename = self._generate_filename(transcript)
                                final_output = Path(self.output_path.get()) / filename
                                
                                # Ensure filename is unique
                                counter = 1
                                while final_output.exists():
                                    base = filename.rsplit('.', 1)[0]
                                    final_output = Path(self.output_path.get()) / f"{base}_{counter}.txt"
                                    counter += 1
                                
                                # Move temp file to final location
                                output_file.rename(final_output)
                                
                                processed_files += 1
                                progress = (processed_files / total_files) * 100
                                self._queue_gui_update(lambda: setattr(self.overall_progress, 'value', progress))
                                self._update_status(f"Saved transcript to {final_output.name}")
                                
                        except OpenAIError as e:
                            error_msg = f"OpenAI API error processing {current_file.name}: {str(e)}"
                            logger.error(error_msg)
                            self._update_status(error_msg)
                            if "rate limit" in str(e).lower():
                                time.sleep(60)  # Wait longer for rate limits
                                
                        except IOError as e:
                            error_msg = f"File error processing {current_file.name}: {str(e)}"
                            logger.error(error_msg)
                            self._update_status(error_msg)
                            
                        except Exception as e:
                            error_msg = f"Unexpected error processing {current_file.name}: {str(e)}"
                            logger.error(error_msg, exc_info=True)
                            self._update_status(error_msg)
                            
                        finally:
                            last_api_call = time.time()
                            # Clean up temp file if it exists
                            if output_file.exists():
                                try:
                                    output_file.unlink()
                                except Exception as e:
                                    logger.warning(f"Failed to clean up temp file: {e}")
                    
                except Exception as e:
                    logger.error(f"Critical error processing {current_file}: {e}", exc_info=True)
                    self._update_status(f"Critical error processing {current_file.name}: {str(e)}")
                    
        except Exception as e:
            logger.error(f"Queue processing error: {e}", exc_info=True)
            self._update_status(f"Queue processing error: {str(e)}")
            
        finally:
            self._processing_complete()
        
    def _start_processing(self):
        """Start processing the queue."""
        if not self.file_list.size():
            messagebox.showwarning("No Files", "Please add files to process")
            return
            
        if not self.output_path.get():
            messagebox.showwarning("No Output", "Please select an output directory")
            return
            
        with self.processing_lock:
            if self.processing:
                return  # Already processing
                
            self.processing = True
            self.start_btn.config(state=tk.DISABLED)
            self.cancel_btn.config(state=tk.NORMAL)
            
            # Reset progress
            self.overall_progress['value'] = 0
            self.file_progress['value'] = 0
            self.current_file_label.config(text="")
            
            # Start processing thread
            self.current_thread = threading.Thread(target=self._process_queue)
            self.current_thread.daemon = True  # Make thread daemon so it exits with main thread
            self.current_thread.start()
        
    def _cancel_processing(self):
        """Cancel current processing."""
        with self.processing_lock:
            if not self.processing:
                return
                
            self.processing = False
            self._update_status("Cancelling...")
            
            # Wait for current thread to finish
            if self.current_thread and self.current_thread.is_alive():
                self.current_thread.join(timeout=0.5)  # Give it half a second to clean up
                
    def _processing_complete(self):
        """Clean up after processing is complete."""
        def update():
            with self.processing_lock:
                self.processing = False
                self.current_thread = None
                self.start_btn.config(state=tk.NORMAL)
                self.cancel_btn.config(state=tk.DISABLED)
                self.current_file_label.config(text="")
                self.file_progress['value'] = 0
                self.overall_progress['value'] = 0
            
        self._queue_gui_update(update)
        self._update_status("Processing complete")
        
    def _update_status(self, message: str):
        """Update status text safely across threads."""
        def update():
            try:
                self.status_text.insert(tk.END, f"{message}\n")
                self.status_text.see(tk.END)
                self._cleanup_status_text()
            except Exception as e:
                logger.error(f"Error updating status: {e}")
                
        self._queue_gui_update(update)
        logger.info(message)
        
    def _update_file_progress(self, current: int, total: int):
        """Update file progress safely across threads."""
        def update():
            if total > 0:
                self.file_progress['value'] = (current / total) * 100
                
        self._queue_gui_update(update)
        
    def _cleanup_temp_files(self):
        """Clean up temporary files and directories."""
        try:
            if self.chunks_dir.exists():
                for file in self.chunks_dir.glob("*"):
                    try:
                        if file.is_file():
                            file.unlink()
                        elif file.is_dir():
                            for subfile in file.glob("*"):
                                subfile.unlink()
                            file.rmdir()
                    except Exception as e:
                        logger.warning(f"Failed to clean up {file}: {e}")
                        
            logger.info("Cleaned up temporary files")
            
        except Exception as e:
            logger.error(f"Error cleaning up temp files: {e}")
            
    def _cleanup_status_text(self):
        """Clean up old status messages if too many have accumulated."""
        try:
            current_lines = int(self.status_text.index('end-1c').split('.')[0])
            if current_lines > self.max_status_lines:
                # Keep the last max_status_lines/2 lines
                keep_lines = self.max_status_lines // 2
                self.status_text.delete('1.0', f'{current_lines - keep_lines}.0')
                self.status_text.see(tk.END)
        except Exception as e:
            logger.warning(f"Error cleaning up status text: {e}")
            
    def _on_closing(self):
        """Handle window closing."""
        if self.processing:
            if messagebox.askokcancel("Quit", "Processing in progress. Cancel and quit?"):
                self.processing = False
                # Signal GUI update thread to stop
                self.gui_update_queue.put(None)
                self.gui_update_thread.join(timeout=1.0)
                self._cleanup_temp_files()
                self.window.destroy()
        else:
            # Signal GUI update thread to stop
            self.gui_update_queue.put(None)
            self.gui_update_thread.join(timeout=1.0)
            self._cleanup_temp_files()
            self.window.destroy()
            
    def run(self):
        """Run the application."""
        try:
            self.window.mainloop()
        finally:
            # Signal GUI update thread to stop
            self.gui_update_queue.put(None)
            self.gui_update_thread.join(timeout=1.0)
            self._cleanup_temp_files() 