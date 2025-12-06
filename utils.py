import yt_dlp
import whisper
import os
import re

def extract_audio(youtube_url, output_path="downloads"):
    """
    Downloads audio from a YouTube video using yt-dlp.
    Returns the path to the downloaded audio file and the video title.
    """
    if not os.path.exists(output_path):
        os.makedirs(output_path)

    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': f'{output_path}/%(id)s.%(ext)s',
        'quiet': True,
        'extractor_args': {'youtube': {'player_client': ['web', 'android']}},
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
        },
        'nocheckcertificate': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(youtube_url, download=True)
        video_title = info_dict.get('title', 'Unknown Title')
        video_id = info_dict.get('id')
        duration = info_dict.get('duration')
        file_path = f"{output_path}/{video_id}.mp3"
    
    return file_path, video_title, duration

def transcribe_audio(audio_path, learned_words=None, model_name="turbo"):
    """
    Transcribes audio using OpenAI Whisper.
    Uses 'turbo' (large-v3-turbo) model for high accuracy and speed.
    """
    # Load model 
    model = whisper.load_model(model_name)
    
    # Context-rich prompt
    base_prompt = (
        "이 영상은 선거 공약, 지방 자치, 대통령, 시군구, 광역 단체, 중앙 지방 협력 회의, 법령, 공모 사업, MOU 체결 등 "
        "정치와 행정에 관한 회의 내용입니다. 전문 용어와 문맥을 고려하여 정확하게 받아쓰세요."
    )
    
    # Inject learned words if available
    if learned_words:
        # Join top words to reinforce them. Whisper prompt limit is 244 tokens, so be careful.
        # We assume learned_words are specific entities.
        injected_context = ", ".join(learned_words)
        initial_prompt = f"{base_prompt} 중요 용어: {injected_context}"
    else:
        initial_prompt = base_prompt
    
    result = model.transcribe(
        audio_path, 
        language='ko', 
        initial_prompt=initial_prompt,
        beam_size=5,
        patience=1.0,
        condition_on_previous_text=True
    )
    
    segments = []
    for segment in result['segments']:
        segments.append({
            'start': segment['start'],
            'end': segment['end'],
            'text': segment['text'].strip(),
            'is_completed': False # Default new segments as incomplete
        })
    
    return segments

def group_segments_by_time(segments, interval=60):
    """
    Groups segments into chunks of approximately `interval` seconds.
    Example: 0~60s, 60~120s...
    """
    if not segments:
        return []

    grouped = []
    current_group = {
        'start': segments[0]['start'],
        'end': segments[0]['end'],
        'text': segments[0]['text'],
        'is_completed': False
    }

    for i in range(1, len(segments)):
        seg = segments[i]
        
        current_duration = current_group['end'] - current_group['start']
        
        if current_duration < interval:
            # Append to current
            current_group['end'] = seg['end']
            current_group['text'] += " " + seg['text']
        else:
            # Finalize current and start new
            grouped.append(current_group)
            current_group = {
                'start': seg['start'],
                'end': seg['end'],
                'text': seg['text'],
                'is_completed': False
            }
    
    # Append the last one
    grouped.append(current_group)
    return grouped

def extract_diff_words(original, corrected):
    """
    Compares original and corrected text to find NEW or CHANGED words.
    Returns a set of words that are present in corrected but not in original (or replaced).
    Simple heuristic: Split by spaces, find words in corrected not in original.
    """
    import re
    def clean(s):
        return set(re.findall(r'\w+', s))
    
    org_words = clean(original)
    new_words = clean(corrected)
    
    # Learned words are those in new_words but not in org_words
    learned = new_words - org_words
    return list(learned)
