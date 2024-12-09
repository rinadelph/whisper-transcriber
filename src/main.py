"""
Main entry point for the Whisper Transcriber application.
"""

import os
import sys
from pathlib import Path
import logging
from dotenv import load_dotenv

# Set up logging to be more verbose
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.gui.window import MainWindow

def main():
    """Initialize and run the application."""
    try:
        # Load environment variables
        load_dotenv()
        
        # Get API key
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("Error: OPENAI_API_KEY not found in environment variables.")
            print("Please set it in your .env file.")
            sys.exit(1)
        
        # Set up paths
        base_dir = Path(__file__).parent.parent
        temp_dir = base_dir / "temp"
        
        # Create temp directory if it doesn't exist
        temp_dir.mkdir(exist_ok=True)
        
        # Clean up any existing temp files
        try:
            for file in temp_dir.glob("*"):
                try:
                    if file.is_file():
                        file.unlink()
                    elif file.is_dir():
                        for subfile in file.glob("*"):
                            subfile.unlink()
                        file.rmdir()
                except Exception as e:
                    logging.warning(f"Failed to clean up {file}: {e}")
        except Exception as e:
            logging.warning(f"Failed to clean temp directory: {e}")
        
        # Initialize and run the main window
        window = MainWindow(api_key, temp_dir)
        window.run()
        
    except Exception as e:
        logging.error(f"Application error: {str(e)}", exc_info=True)
        sys.exit(1)
    finally:
        # Final cleanup of temp directory
        try:
            for file in temp_dir.glob("*"):
                try:
                    if file.is_file():
                        file.unlink()
                    elif file.is_dir():
                        for subfile in file.glob("*"):
                            subfile.unlink()
                        file.rmdir()
                except Exception as e:
                    logging.warning(f"Failed to clean up {file}: {e}")
            temp_dir.rmdir()
        except Exception as e:
            logging.warning(f"Failed to cleanup temp directory: {str(e)}")

if __name__ == "__main__":
    main() 