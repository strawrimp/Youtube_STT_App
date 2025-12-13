from db_manager import DBManager
from utils import transcribe_audio, group_segments_by_time
import os

# Mapping based on previous yt-dlp checks
TARGETS = [
    {"id": "TQs9WMYSX80", "title": "250719 23기 공동체학교 1-3"},
    {"id": "pxGariv844U", "title": "250809 23기 공동체학교 2-1"},
    {"id": "ZqE3pnnc314", "title": "250809 23기 공동체학교 2-2"},
    {"id": "-IAecS1KUoI", "title": "250809 23기 공동체학교 2-3"}
]

def target_restore():
    db = DBManager('editor.db')
    
    # Check what's already in DB
    existing_urls = [p['youtube_url'] for p in db.get_active_projects()]
    existing_ids = []
    for url in existing_urls:
         if "v=" in url:
             existing_ids.append(url.split("v=")[1])
         else:
             existing_ids.append(url)

    print(f"Existing Active IDs: {existing_ids}")

    for target in TARGETS:
        vid = target['id']
        title = target['title']
        
        if vid in existing_ids:
            print(f"⏭️ Skipping {title} ({vid}) - Already Active")
            continue
            
        print(f"🚀 Starting Recovery for: {title} ({vid})")
        
        # Look for file
        # Can be .mp3 or .mp4 etc.
        files = [f for f in os.listdir("downloads") if f.startswith(vid)]
        if not files:
            print(f"   ❌ File not found for {vid}")
            continue
            
        file_path = os.path.join("downloads", files[0])
        print(f"   📂 Found file: {file_path}")
        
        try:
            print(f"   🎙️ Transcribing {title}...")
            # Transcribe
            segments = transcribe_audio(file_path)
            grouped = group_segments_by_time(segments)
            
            # Save
            url = f"https://www.youtube.com/watch?v={vid}"
            pid = db.create_project(url, title, 0, assignee=None)
            db.save_subtitles(pid, grouped)
            print(f"   ✅ Success! Restored as ID {pid}")
            
        except Exception as e:
            print(f"   ❌ Error restoring {title}: {e}")

if __name__ == "__main__":
    target_restore()
