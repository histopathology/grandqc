import os
import sys
import time
import logging
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class SVSHandler(FileSystemEventHandler):
    def __init__(self, input_dir, output_dir):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.processed_files = set()
        
        # Initialize logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(message)s',
            handlers=[
                logging.FileHandler(os.path.join(output_dir, 'grandqc_watchdog.log')),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def on_created(self, event):
        if event.is_directory:
            return
        
        if event.src_path.lower().endswith('.svs'):
            file_path = event.src_path
            file_name = os.path.basename(file_path)
            
            # Check if file was already processed
            if file_path in self.processed_files:
                self.logger.info(f"File {file_name} was already processed. Skipping...")
                return
                
            self.logger.info(f"New .svs file detected: {file_name}")
            
            # Wait for file to be completely written
            file_size = -1
            while True:
                try:
                    current_size = os.path.getsize(file_path)
                    if current_size == file_size:
                        break
                    file_size = current_size
                    time.sleep(1)  # Wait 1 second before checking again
                except OSError:
                    self.logger.error(f"Error accessing file {file_name}. File may be in use.")
                    return

            try:
                # Run tissue detection first
                self.logger.info(f"Running tissue detection on {file_name}")
                subprocess_env = os.environ.copy()
                subprocess.run([
                    "python", 
                    "wsi_tis_detect.py",
                    "--slide_folder", self.input_dir,
                    "--output_dir", self.output_dir
                ], env=subprocess_env, check=True)

                # Then run artifact detection
                self.logger.info(f"Running artifact detection on {file_name}")
                subprocess.run([
                    "python", 
                    "main.py",
                    "--slide_folder", self.input_dir,
                    "--output_dir", self.output_dir
                ], env=subprocess_env, check=True)

                self.processed_files.add(file_path)
                self.logger.info(f"Successfully processed {file_name}")
                
            except subprocess.CalledProcessError as e:
                self.logger.error(f"Error processing {file_name}: {str(e)}")
            except Exception as e:
                self.logger.error(f"Unexpected error processing {file_name}: {str(e)}")

def start_watching(input_dir, output_dir):
    """
    Start watching the input directory for new .svs files
    
    Args:
        input_dir (str): Directory to watch for new .svs files
        output_dir (str): Directory where GrandQC outputs will be saved
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Initialize event handler and observer
    event_handler = SVSHandler(input_dir, output_dir)
    observer = Observer()
    observer.schedule(event_handler, input_dir, recursive=False)
    observer.start()
    
    print(f"Watching directory {input_dir} for new .svs files...")
    print(f"Output will be saved to {output_dir}")
    print("Press Ctrl+C to stop")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\nStopping watchdog...")
    observer.join()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python watchdog_grandqc.py <input_directory> <output_directory>")
        sys.exit(1)
        
    input_dir = os.path.abspath(sys.argv[1])
    output_dir = os.path.abspath(sys.argv[2])
    
    if not os.path.exists(input_dir):
        print(f"Input directory {input_dir} does not exist!")
        sys.exit(1)
        
    start_watching(input_dir, output_dir)
