import os
import json

def _get_notes_path(folder: str) -> str:
    path = os.path.expanduser(folder)
    os.makedirs(path, exist_ok=True)  # create folder if it doesn't exist
    return os.path.join(path, "notes.json")

def load_notes(folder: str) -> list:
    """
    Loads notes from disk. Returns a list of strings.
    Returns an empty list if no file exists yet.
    """
    path = _get_notes_path(folder)
    if not os.path.exists(path):
        return []
    with open(path, "r") as f:
        return json.load(f)

def save_notes(folder: str, notes: list) -> None:
    """
    Saves the current list of notes to disk as JSON.
    Overwrites the previous file completely.
    """
    path = _get_notes_path(folder)
    with open(path, "w") as f:
        json.dump(notes, f, indent=2)
