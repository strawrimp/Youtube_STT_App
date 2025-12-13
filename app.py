import streamlit as st
import pandas as pd
import time
import os
from db_manager import DBManager
from utils import extract_audio, transcribe_audio, group_segments_by_time, extract_diff_words

# --- Setup & Styling ---
APP_TITLE = "오늘 녹취록"
st.set_page_config(page_title=APP_TITLE, layout="wide", initial_sidebar_state="auto")

# --- Custom CSS: Modern Dark Studio Theme ---
st.markdown("""
<style>
    @import url("https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.min.css");

    /* Global Typography - Apply to body and text elements, NOT icons */
    html, body, [class*="css"] {
        font-family: 'Pretendard', sans-serif;
    }

    /* 1. Dark Studio Theme Backgrounds */
    .stApp {
        background-color: #0E1117; /* Deepest Dark */
        color: #E0E0E0;
    }
    
    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #161B22;
        border-right: 1px solid #30363D;
    }

    /* 2. Sticky Video Player Container */
    .sticky-video-container {
        position: sticky;
        top: 0;
        z-index: 999;
        background-color: #0E1117;
        padding-bottom: 20px;
        padding-top: 10px;
        border-bottom: 1px solid #30363D;
        margin-bottom: 20px;
    }

    /* 3. Text Area Styling (Eye Comfort) */
    .stTextArea textarea {
        background-color: #262730 !important;
        color: #E0E0E0 !important;
        border: 1px solid #41454C !important;
        border-radius: 8px !important;
        font-size: 1.05rem;
        line-height: 1.6;
    }
    .stTextArea textarea:focus {
        border: 1px solid #FF4B4B !important; /* Primary Focus */
        box-shadow: 0 0 0 1px #FF4B4B !important;
    }
    
    /* Disabled Text Area */
    .stTextArea textarea:disabled {
        background-color: #1a1d21 !important;
        color: #6e7681 !important;
        border-color: #30363d !important;
        opacity: 0.7;
    }
    
    /* 4. Buttons (Modern Radius & Transition) */
    .stButton > button {
        border-radius: 8px !important;
        transition: all 0.2s ease-in-out !important;
        border: none !important;
        font-weight: 500 !important;
    }
    
    /* Sidebar Project List Button */
    .sidebar-project-btn > button {
        text-align: left;
        height: auto;
        padding-top: 10px;
        padding-bottom: 10px;
    }
    
    /* Sidebar Delete Button Styling */
    .delete-btn {
        display: flex;
        align-items: center;
        justify-content: center;
        height: 100%;
    }
    .delete-btn button {
        background-color: transparent !important;
        color: #9CA3AF !important;
        border: 1px solid #374151 !important;
        padding: 4px 8px !important;
        margin: 0 !important;
    }
    .delete-btn button:hover {
        background-color: #374151 !important;
        color: #EF4444 !important; /* Red on hover */
        border-color: #EF4444 !important;
    }

    button[kind="primary"] {
        background-color: #FF4B4B !important;
        color: white !important;
    }
    button[kind="primary"]:hover {
        background-color: #FF2B2B !important;
    }

    /* Status Icons in Sidebar */
    .status-icon {
        font-size: 1.2rem;
        margin-right: 8px;
    }
    
    /* Force Vertical Alignment in Sidebar Columns (CSS fallback) */
    section[data-testid="stSidebar"] div[data-testid="stHorizontalBlock"] {
        align-items: center !important;
    }
    
    /* Remove margins and borders from all sidebar buttons for clean alignment */
    section[data-testid="stSidebar"] button {
        margin-top: 0px !important;
        margin-bottom: 0px !important;
        border: none !important;
    }

    /* Ensure specific alignment for the delete button container if needed */
    [data-testid="stSidebar"] [data-testid="column"]:nth-of-type(2) {
        display: flex !important;
        flex-direction: column !important;
        justify-content: center !important;
        align-items: center !important;
    }

    /* Hide keyboard arrow text if mistakenly rendered */
    .stMarkdown p {
        margin-bottom: 0px;
    }
    /* Specifically hide the material icon text if it leaks */
    /* This targets common patterns for leaked icon text */
    body:contains('keybord-arrow') {
         font-size: 0;
    }

</style>
""", unsafe_allow_html=True)

# --- State Initialization ---
if 'db_manager' not in st.session_state:
    try:
        st.session_state.db_manager = DBManager('editor.db')
        st.session_state.db = st.session_state.db_manager
    except Exception as e:
        st.error(f"DB Error: {e}")

if 'current_project_id' not in st.session_state:
    st.session_state.current_project_id = None

if 'video_start_time' not in st.session_state:
    st.session_state.video_start_time = 0

if 'subtitles' not in st.session_state:
    st.session_state.subtitles = []

if 'nickname' not in st.session_state:
    st.session_state.nickname = ""

# --- Sidebar ---
st.sidebar.title("오늘기록원")

# 0. User Name
st.session_state.nickname = st.sidebar.text_input("👤 이름", value=st.session_state.nickname, placeholder="이름을 입력하세요 (필수)")
st.sidebar.markdown("---")


# 1. History (작업 목록)
st.sidebar.markdown("### 📂 작업 리스트")
projects = st.session_state.db.get_all_projects()

for p in projects:
    # Improved Alignment for Sidebar
    # Try to use vertical_alignment if supported (Streamlit 1.35+)
    try:
        c1, c2 = st.sidebar.columns([0.85, 0.15], vertical_alignment="center")
    except TypeError:
        # Fallback for older versions
        c1, c2 = st.sidebar.columns([0.85, 0.15])
    
    # Status Icon & Progress
    status_icon = p.get('status', '⚪')
    progress_pct = p.get('progress_pct', 0)
    
    with c1:
        date_str = p.get('created_at', pd.Timestamp.now()).strftime("%m/%d %H:%M")
        assignee_str = f"| {p['assignee']}" if p.get('assignee') else ""
        # Format: 🟢 Title (10%) | Nickname
        label = f"{status_icon} {p['title']} ({progress_pct}%) {assignee_str}"
        
        # Use a custom class for styling if needed, mainly relying on Streamlit's full width
        if st.button(label, key=f"hist_{p['id']}", use_container_width=True):
            # Reset and Load
            keys_to_reset = ['subtitles', 'video_start_time', 'original_subtitles_map']
            for k in keys_to_reset:
                if k in st.session_state:
                    del st.session_state[k]
                    
            st.session_state.current_project_id = p['id']
            loaded_subs = st.session_state.db.get_subtitles(p['id'])
            st.session_state.subtitles = loaded_subs
            st.session_state.original_subtitles_map = {s['id']: s['text'] for s in loaded_subs}
            st.rerun()
            
    with c2:
        # Delete Button with Custom Styling Class
        st.markdown('<div class="delete-btn">', unsafe_allow_html=True)
        if st.button("✖", key=f"del_{p['id']}", help="삭제"):
            st.session_state.db.delete_project(p['id'])
            if st.session_state.current_project_id == p['id']:
                st.session_state.current_project_id = None
                st.session_state.subtitles = []
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

st.sidebar.markdown("---")
with st.sidebar.expander("📋 전체 텍스트 복사하기"):
    if st.session_state.subtitles:
        full_text = "\n\n".join([s['text'] for s in st.session_state.subtitles])
        st.code(full_text, language='text')
    else:
        st.caption("작업 중인 내용이 없습니다.")


# --- Main Content ---
if not st.session_state.current_project_id:
    # --- Landing / New Project ---
    st.title("🎙️ " + APP_TITLE)
    st.markdown("### 전문적인 녹취록 작성을 위한 스튜디오")
    
    with st.container(border=True):
        st.subheader("새 프로젝트 시작하기")
        url_input = st.text_input("YouTube URL 입력", placeholder="https://youtube.com/...")
        
        # New Project Logic with Assignee
        if st.button("영상 분석 시작", type="primary", use_container_width=True):
            if not url_input:
                st.warning("URL을 입력해주세요.")
            elif not st.session_state.nickname:
                st.warning("작업자 이름을 먼저 입력해주세요 (왼쪽 사이드바).")
            else:
                with st.spinner("⏳ 영상을 분석하고 초안을 작성 중입니다..."):
                    try:
                        audio_path, title, duration = extract_audio(url_input)
                        # Create with assignee
                        proj_id = st.session_state.db.create_project(url_input, title, duration, assignee=st.session_state.nickname)
                        st.session_state.current_project_id = proj_id
                        
                        learned_words = st.session_state.db.get_learned_words()
                        raw_segments = transcribe_audio(audio_path, learned_words=learned_words)
                        grouped_segments = group_segments_by_time(raw_segments, interval=60)
                        
                        st.session_state.db.save_subtitles(proj_id, grouped_segments)
                        
                        loaded_subs = st.session_state.db.get_subtitles(proj_id)
                        st.session_state.subtitles = loaded_subs
                        st.session_state.original_subtitles_map = {s['id']: s['text'] for s in loaded_subs}
                        
                        st.success(f"프로젝트 '{title}' 생성 완료! 담당자: {st.session_state.nickname}")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"오류 발생: {e}")

else:
    # --- Editor Mode ---
    project = st.session_state.db.get_project(st.session_state.current_project_id)
    
    # Access Control Logic
    # 1. Name is REQUIRED for any editing
    # 2. Allow edit if: PROJECT has no assignee OR matches current user
    # 3. If project has assignee AND current user != assignee -> Read Only (disabled)
    
    is_name_entered = bool(st.session_state.nickname.strip())
    is_editable = False
    read_only_reason = None
    
    if not is_name_entered:
        read_only_reason = "이름을 입력해야 수정할 수 있습니다."
    elif project.assignee and project.assignee != st.session_state.nickname:
        read_only_reason = f"담당자({project.assignee})만 수정할 수 있습니다."
    else:
        is_editable = True
    
    # Toast for status
    if not is_editable and read_only_reason:
        st.toast(f"🔒 {read_only_reason}", icon="🔒")
    
    # 1. Sticky Video Header
    st.markdown('<div class="sticky-video-container">', unsafe_allow_html=True)
    st.subheader(f"Editing: {project.title}")
    st.video(project.youtube_url, start_time=st.session_state.video_start_time)
    st.markdown('</div>', unsafe_allow_html=True)

    # 2. Controls Row
    col_ctrl1, col_ctrl2 = st.columns([6, 2])
    with col_ctrl1:
        if is_editable:
            st.caption("아래 자막을 수정하면 자동 저장됩니다.")
        else:
            st.warning(f"🔒 {read_only_reason}")
            
    with col_ctrl2:
        if is_editable:
            if st.button("💾 저장 및 학습", type="primary", use_container_width=True):
                # Smart Save
                new_learned_words = []
                if 'original_subtitles_map' in st.session_state:
                    for sub in st.session_state.subtitles:
                        orig_text = st.session_state.original_subtitles_map.get(sub['id'], "")
                        if orig_text and orig_text != sub['text']:
                            diffs = extract_diff_words(orig_text, sub['text'])
                            new_learned_words.extend(diffs)
                
                if new_learned_words:
                    st.session_state.db.add_learned_words(new_learned_words)
                    st.toast(f"🧠 {len(new_learned_words)}개 단어를 새로 학습했습니다!", icon="🧠")
                
                st.session_state.db.save_subtitles(project.id, st.session_state.subtitles)
                st.session_state.original_subtitles_map = {s['id']: s['text'] for s in st.session_state.subtitles}
                st.toast("저장 완료!", icon="✅")
        else:
             st.button("💾 저장 불가", disabled=True, use_container_width=True)

    # 3. Independent Scrollable Editor Area
    updated_subs = []
    has_changes = False
    
    with st.container(height=700):
        # Iterate Subtitles
        for i, sub in enumerate(st.session_state.subtitles):
            
            # Layout: [0.15, 0.85] as requested
            c1, c2 = st.columns([0.15, 0.85])
            
            start_seconds = sub['start']
            start_str = time.strftime('%M:%S', time.gmtime(start_seconds))
            
            with c1:
                # Time Button (Primary Accent)
                if st.button(f"⏱ {start_str}", key=f"seek_{project.id}_{i}", help="재생 위치 이동"):
                    st.session_state.video_start_time = int(start_seconds)
                    st.rerun()
                
                # Checkbox
                # Only editable if user has permission
                is_complete = st.checkbox(
                    "완료", 
                    value=sub.get('is_completed', False), 
                    key=f"chk_{project.id}_{i}",
                    label_visibility="visible",
                    disabled=not is_editable
                )
                if is_complete != sub.get('is_completed', False):
                    sub['is_completed'] = is_complete
                    has_changes = True
                    st.rerun()

            with c2:
                # Text Area
                # Full width
                val = st.text_area(
                    label=f"내용 수정 ({start_str} ~)",
                    value=sub['text'],
                    key=f"text_{project.id}_{i}",
                    label_visibility="collapsed",
                    height=120,
                    disabled=not is_editable
                )
                if val != sub['text']:
                    sub['text'] = val
                    has_changes = True
            
            st.markdown("---") # Divider
            updated_subs.append(sub)

    # Auto-save Logic
    if has_changes and is_editable:
        st.session_state.subtitles = updated_subs
        st.session_state.db.save_subtitles(project.id, updated_subs)
