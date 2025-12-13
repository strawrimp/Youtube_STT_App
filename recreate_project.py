from db_manager import DBManager
from utils import extract_audio, transcribe_audio, group_segments_by_time
import os

db = DBManager('editor.db')
url = "https://www.youtube.com/watch?v=eymDzt3M8pk"
print(f"Restoring project from URL: {url}")

try:
    print("1. Extracting/Downloading Audio...")
    # This will handle re-downloading since the existing file is .part
    path, title, duration = extract_audio(url)
    print(f"   Title: {title}")
    
    print("2. Transcribing (this may take a while)...")
    segments = transcribe_audio(path)
    
    print("3. Grouping segments...")
    grouped = group_segments_by_time(segments)
    
    print("4. Saving to DB...")
    # Assign to None (Unassigned) or specific user if known? 
    # Let's leave unassigned so it appears in 'Waiting'.
    pid = db.create_project(url, title, duration, assignee=None)
    db.save_subtitles(pid, grouped)
    
    print(f"✅ Success! Project ID: {pid}")

except Exception as e:
    print(f"❌ Error: {e}")
