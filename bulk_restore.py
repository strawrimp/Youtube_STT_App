import os
import glob
from db_manager import DBManager
from utils import transcribe_audio, group_segments_by_time
import yt_dlp

def get_video_title(video_id):
    url = f"https://www.youtube.com/watch?v={video_id}"
    ydl_opts = {
        'quiet': True,
        'ignoreerrors': True,
        'nocheckcertificate': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info.get('title') if info else None
    except:
        return None

def bulk_restore():
    db = DBManager('editor.db')
    
    # Get existing video IDs from DB
    existing_urls = [p['youtube_url'] for p in db.get_all_projects()]
    existing_ids = []
    for url in existing_urls:
         if "v=" in url:
             existing_ids.append(url.split("v=")[1])
         else:
             existing_ids.append(url) # fallback

    print(f"Existing in DB: {existing_ids}")

    # Scan downloads folder
    audio_files = glob.glob("downloads/*.mp3")
    
    for file_path in audio_files:
        filename = os.path.basename(file_path)
        video_id = filename.replace(".mp3", "")
        
        # Skip if already exists
        if video_id in existing_ids:
            print(f"⏭️ Skipping {video_id} (Already exists)")
            continue
            
        print(f"🔄 Restoring {video_id}...")
        
        # 1. Fetch Title
        title = get_video_title(video_id)
        if not title:
            title = f"Restored Video {video_id}"
            print(f"   ⚠️ Could not fetch title, using: {title}")
        else:
            print(f"   Found Title: {title}")
            
        # 2. Transcribe
        try:
            print(f"   🎙️ Transcribing...")
            segments = transcribe_audio(file_path)
            grouped = group_segments_by_time(segments)
            
            # 3. Save to DB
            duration = 0 # Can't easily get duration without probing file, but acceptable.
            url = f"https://www.youtube.com/watch?v={video_id}"
            
            pid = db.create_project(url, title, duration, assignee=None)
            db.save_subtitles(pid, grouped)
            
            print(f"   ✅ Restored as Project ID {pid}")
            
        except Exception as e:
            print(f"   ❌ Failed to transcribe: {e}")

if __name__ == "__main__":
    bulk_restore()
