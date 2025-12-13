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
            return info.get('title') if info else "Unknown"
    except Exception as e:
        return f"Error: {e}"

ids = ["rdZ7YyOr5yI", "W4-QfsaEg_I", "eymDzt3M8pk", "46Kt8TPsw6U"]

print("Checking titles...")
for vid in ids:
    title = get_video_title(vid)
    print(f"ID: {vid} -> Title: {title}")
