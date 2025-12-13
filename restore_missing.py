from db_manager import DBManager
from utils import transcribe_audio, group_segments_by_time
import os
import glob

# Mapping Confirmed
TARGETS = [
    {"id": "rdZ7YyOr5yI", "title": "250816 23기 공동체학교 3-1"},
    {"id": "W4-QfsaEg_I", "title": "250816 23기 공동체학교 3-2"},
    {"id": "eymDzt3M8pk", "title": "250816 23기 공동체학교 3-3"},
    {"id": "ZqE3pnnc314", "title": "250809 23기 공동체학교 2-2"},
    {"id": "-IAecS1KUoI", "title": "250809 23기 공동체학교 2-3"}
]

def restore_missing():
    db = DBManager('editor.db')
    existing_urls = [p['youtube_url'] for p in db.get_all_projects()]
    
    existing_ids = []
    for url in existing_urls:
         if "v=" in url:
             existing_ids.append(url.split("v=")[1])
         else:
             existing_ids.append(url)

    print(f"Existing IDs count: {len(existing_ids)}")

    for target in TARGETS:
        vid = target['id']
        title = target['title']
        
        if vid in existing_ids:
            print(f"⏭️ Skipping {title} ({vid}) - Already Active")
            continue
            
        print(f"\n🚀 Restoring: {title} ({vid})")
        
        # Check for file
        # Use glob to find mp3
        files = glob.glob(f"downloads/{vid}*.mp3")
        if not files:
            files = glob.glob(f"downloads/{vid}*.mp4")
            
        if not files:
            print(f"   ❌ File not found for {vid}")
            continue
            
        file_path = files[0]
        print(f"   📂 Found file: {file_path}")
        
        try:
            print(f"   🎙️ Transcribing...")
            segments = transcribe_audio(file_path)
            grouped = group_segments_by_time(segments)
            
            # Save
            url = f"https://www.youtube.com/watch?v={vid}"
            pid = db.create_project(url, title, 0)
            db.save_subtitles(pid, grouped)
            print(f"   ✅ Success! Restored as Project ID {pid}")
            
        except Exception as e:
            print(f"   ❌ Error restoring {title}: {e}")

if __name__ == "__main__":
    restore_missing()
