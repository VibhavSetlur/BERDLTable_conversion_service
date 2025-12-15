#!/usr/bin/env python3
import sys
import os
import json
import configparser
from pathlib import Path

# Setup paths
current_dir = Path(__file__).resolve().parent
repo_root = current_dir.parents[1]
lib_path = repo_root / "lib"

sys.path.append(str(lib_path))

try:
    from installed_clients.kbutillib.kb_ws_utils import KBWSUtils
    from installed_clients.kbutillib.notebook_utils import NotebookUtils
except ImportError as e:
    print(f"Error importing KBUtilLib from installed_clients: {e}")
    sys.exit(1)

class NotebookUtil(NotebookUtils, KBWSUtils):
    def __init__(self, **kwargs):
        super().__init__(
            notebook_folder=str(current_dir),
            name="KBWSUtils Example",
            kb_version="appdev",
            **kwargs
        )

def get_token_from_config():
    config_path = repo_root / "test_local" / "test.cfg"
    if not config_path.exists():
        return None
    
    # Simple parsing because ConfigParser needs headers
    try:
        content = config_path.read_text()
        # Add a fake header to make ConfigParser happy
        parser = configparser.ConfigParser()
        parser.read_string("[DEFAULT]\n" + content)
        return parser["DEFAULT"].get("test_token")
    except Exception as e:
        print(f"Error reading config: {e}")
        return None

def main():
    token = os.environ.get("KB_AUTH_TOKEN")
    if not token:
        token = get_token_from_config()
    
    if not token:
        print("ERROR: KB_AUTH_TOKEN not set and test_local/test.cfg' includes no test_token.")
        sys.exit(1)

    print(f"Initializing NotebookUtil (AppDev)...")
    try:
        nu = NotebookUtil(token=token)
    except Exception as e:
        print(f"Failed to initialize: {e}")
        sys.exit(1)

    ws_id = 76990
    obj_name = "ADPITest"
    
    print(f"Fetching object info for {ws_id}/{obj_name}...")
    try:
        # get_object returns the data part
        obj_data = nu.get_object(obj_name, ws=ws_id)
        
        print("\nObject Keys:")
        print(list(obj_data.keys()))
        
        # Check for 'shock_id' or 'handle'
        # BERDLTable likely has 'shock_id' or similar pointing to the SQLite file
        print("\nStructure Snippet (Top Level):")
        for k, v in obj_data.items():
            if isinstance(v, (str, int, float, bool)):
                print(f"  {k}: {v}")
            elif isinstance(v, dict) and "id" in v and "url" in v: # Handle check
                print(f"  {k}: [Handle] {v['id']}")
            else:
                print(f"  {k}: {type(v).__name__}")
                
    except Exception as e:
        print(f"Error fetching object: {e}")

if __name__ == "__main__":
    main()
