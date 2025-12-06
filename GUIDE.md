# 🎥 Advanced Subtitle Editor - User Guide

This guide explains how to set up and run your new "Advanced Subtitle Editor" application.

## 🚀 1. Installation

### Prerequisites
- **Python 3.8+** installed.
- **FFmpeg** installed (required for Whisper & yt-dlp).
  - *Mac (Homebrew)*: `brew install ffmpeg`
  - *Windows*: Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH.

### Setup Steps
1. **Navigate to the project folder**:
   ```bash
   cd /Volumes/Dock/안티그래비티/Youtube_STT_App
   ```

2. **Install Python Libraries**:
   ```bash
   pip install -r requirements.txt
   ```

3. **(Optional) Set Gemini API Key**:
   To use the **AI Review** feature, you need a Google Gemini API key.
   - You can set it as an environment variable:
     ```bash
     export GEMINI_API_KEY="your_api_key_here"
     ```
   - Or the app will prompt you / show a warning if it's missing when you try to use the AI feature.

## ▶️ 2. Running the App

Run the following command in your terminal:
```bash
streamlit run app.py
```

The application will open in your default web browser (usually at `http://localhost:8501`).

## 🛠 Features Guide

### 1. Start a New Project
- Enter a **YouTube URL** in the main input field.
- Click **"Analyze Video"**.
- The app will:
  - Download the audio.
  - Transcribe it using OpenAI Whisper.
  - Apply any "Custom Dictionary" rules you have saved.
  - Create a new project in the database.

### 2. Editor Interface
- **Video Player**: Located at the top. Shows the YouTube video.
- **Subtitle List**: Below the player.
  - **Timestamp**: Click the **▶️ Play** button next to any line to jump the video to that exact moment.
  - **Text Box**: Edit the text directly. Changes are **auto-saved** to the database when you click away or press Enter (Ctrl+Enter).
- **AI Review**: Click the "✨ AI Review (Gemini)" button to have Gemini analyze the text for typos or odd phrasing.

### 3. Sidebar Features
- **Dictionary**: Add rules to automatically correct persistent errors (e.g., "goggle" -> "Google"). These specific corrections run automatically on **new** imports.
- **History**: Click any past project to reload it and continue working.

## ⚠️ Troubleshooting
- **FFmpeg Error**: If you see an error about "ffmpeg not found", ensure FFmpeg is installed and in your system PATH.
- **Whisper Speed**: The first run might be slow as it downloads the model. It uses the `base` model by default.
