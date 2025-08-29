#!/usr/bin/env python3
"""
Beautiful YouTube Downloader Streamlit App
A modern, aesthetic interface for downloading YouTube videos and playlists.
"""

import streamlit as st
import os
import sys
import tempfile
import shutil
from pathlib import Path
import yt_dlp
import json
from typing import List, Dict, Optional
import time
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="YouTube Downloader Pro",
    page_icon="🎥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for beautiful styling
st.markdown("""
<style>
    /* Main container styling */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem 0;
        text-align: center;
        border-radius: 10px;
        margin-bottom: 2rem;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
    }

    .feature-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
        border-left: 4px solid #667eea;
        margin: 1rem 0;
    }

    .success-box {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        color: white;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
        margin: 1rem 0;
    }

    .error-box {
        background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
        color: white;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
        margin: 1rem 0;
    }

    .info-box {
        background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }

    /* Sidebar styling */
    .sidebar .sidebar-content {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    }

    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 2rem;
        font-weight: bold;
        transition: all 0.3s ease;
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2);
    }

    /* Progress bar styling */
    .stProgress .st-bo {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'download_history' not in st.session_state:
    st.session_state.download_history = []
if 'current_download' not in st.session_state:
    st.session_state.current_download = None

def get_output_directory():
    """Get the output directory for downloads"""
    return os.path.join(os.getcwd(), "Downloads")

def create_download_options(quality="best", audio_only=False, subtitle_langs=None, custom_format=None):
    """Create yt-dlp options based on user preferences"""
    output_dir = get_output_directory()
    os.makedirs(output_dir, exist_ok=True)

    outtmpl = os.path.join(output_dir, "%(title)s [%(id)s].%(ext)s")

    ydl_opts = {
        'outtmpl': outtmpl,
        'ignoreerrors': True,
        'no_warnings': False,
        'extractflat': False,
    }

    if audio_only:
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        })
    else:
        if custom_format:
            ydl_opts['format'] = custom_format
        elif quality == "4K":
            ydl_opts['format'] = 'bestvideo[height<=2160]+bestaudio/best[height<=2160]'
        elif quality == "1440p":
            ydl_opts['format'] = 'bestvideo[height<=1440]+bestaudio/best[height<=1440]'
        elif quality == "1080p":
            ydl_opts['format'] = 'bestvideo[height<=1080]+bestaudio/best[height<=1080]'
        elif quality == "720p":
            ydl_opts['format'] = 'bestvideo[height<=720]+bestaudio/best[height<=720]'
        elif quality == "480p":
            ydl_opts['format'] = 'bestvideo[height<=480]+bestaudio/best[height<=480]'
        else:  # Best Available - Force 1080p as highest priority
            ydl_opts['format'] = 'bestvideo[height<=1080]+bestaudio/bestvideo*+bestaudio/best'

    # Subtitles
    if subtitle_langs:
        ydl_opts.update({
            'writesubtitles': True,
            'subtitleslangs': subtitle_langs,
            'writeautomaticsub': True,
        })

    return ydl_opts

def get_video_info(url):
    """Get video information without downloading"""
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extractflat': False,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info
    except Exception as e:
        return None

def get_available_formats(url):
    """Get available formats for a video"""
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'listformats': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if info and 'formats' in info and info['formats']:
                # Filter and organize formats
                video_formats = []
                audio_formats = []

                for fmt in info['formats']:
                    if fmt.get('vcodec') != 'none' and fmt.get('acodec') == 'none':
                        # Video only
                        video_formats.append(fmt)
                    elif fmt.get('acodec') != 'none' and fmt.get('vcodec') == 'none':
                        # Audio only
                        audio_formats.append(fmt)

                return {
                    'video_formats': video_formats,
                    'audio_formats': audio_formats,
                    'combined_formats': [f for f in info['formats'] if f.get('vcodec') != 'none' and f.get('acodec') != 'none']
                }
        return None
    except Exception as e:
        return None

def format_filesize(size_bytes):
    """Convert bytes to human readable format"""
    if not size_bytes:
        return "Unknown"
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f}{unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f}TB"

def get_format_display(fmt):
    """Get display string for format"""
    resolution = f"{fmt.get('width', '?')}x{fmt.get('height', '?')}"
    if fmt.get('height'):
        resolution = f"{fmt.get('height')}p"

    codec = fmt.get('vcodec', fmt.get('acodec', 'unknown'))
    if codec and len(codec) > 15:
        codec = codec[:12] + "..."

    filesize = format_filesize(fmt.get('filesize'))

    return f"Format {fmt.get('format_id', '?')} - {resolution} - {codec} - {filesize}"

def download_video(url, options):
    """Download video with given options"""
    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            ydl.download([url])
        return True, None
    except Exception as e:
        return False, str(e)

# Header
st.markdown("""
<div class="main-header">
    <h1>🎥 YouTube Downloader Pro</h1>
    <p>Download videos, playlists, and audio with style and ease</p>
</div>
""", unsafe_allow_html=True)

# Sidebar
st.sidebar.markdown("### ⚙️ Settings")

# Download mode selection
download_mode = st.sidebar.selectbox(
    "🎯 Download Mode",
    ["Single Video", "Playlist", "Audio Only", "Batch URLs"]
)

# Quality settings
if download_mode != "Audio Only":
    quality = st.sidebar.selectbox(
        "🎬 Video Quality",
        ["Best Available", "4K", "1440p", "1080p", "720p", "480p", "Custom Format"]
    )
else:
    quality = "audio"

# Advanced format selection
use_custom_format = (quality == "Custom Format")
if use_custom_format:
    st.sidebar.markdown("**🔧 Advanced Format Selection**")
    custom_format_input = st.sidebar.text_input(
        "Format String",
        placeholder="e.g., 137+251 or bestvideo[height<=720]+bestaudio",
        help="Enter yt-dlp format string. Use format preview below to get format IDs."
    )
else:
    custom_format_input = None

# Audio format for audio-only downloads
if download_mode == "Audio Only":
    audio_format = st.sidebar.selectbox(
        "🎵 Audio Format",
        ["MP3", "M4A", "FLAC", "WAV"]
    )

# Subtitle options
download_subtitles = st.sidebar.checkbox("📝 Download Subtitles")
if download_subtitles:
    subtitle_langs = st.sidebar.multiselect(
        "🌍 Subtitle Languages",
        ["en", "es", "fr", "de", "ja", "ko", "zh", "ar", "hi", "ru"],
        default=["en"]
    )
else:
    subtitle_langs = None

# Additional options
embed_metadata = st.sidebar.checkbox("📊 Embed Metadata")
embed_thumbnail = st.sidebar.checkbox("🖼️ Embed Thumbnail")
write_thumbnail = st.sidebar.checkbox("💾 Save Thumbnail File")

# Main content area
col1, col2 = st.columns([2, 1])

with col1:
    if download_mode == "Single Video":
        st.markdown("### 🎬 Single Video Download")

        url = st.text_input(
            "Enter YouTube URL:",
            placeholder="https://www.youtube.com/watch?v=..."
        )

        # Create three columns for buttons
        col_btn1, col_btn2, col_btn3 = st.columns(3)

        with col_btn1:
            show_info = st.button("📋 Preview Video Info")
        with col_btn2:
            show_formats = st.button("🎛️ Show Available Formats")
        with col_btn3:
            download_btn = st.button("⬬ Download Video", type="primary")

        if url and show_info:
            with st.spinner("Fetching video information..."):
                info = get_video_info(url)

                if info:
                    st.markdown("#### 📺 Video Information")

                    col_info1, col_info2 = st.columns(2)

                    with col_info1:
                        st.markdown(f"**Title:** {info.get('title', 'N/A')}")
                        st.markdown(f"**Channel:** {info.get('uploader', 'N/A')}")
                        st.markdown(f"**Duration:** {info.get('duration_string', 'N/A')}")

                    with col_info2:
                        st.markdown(f"**Views:** {info.get('view_count', 'N/A'):,}")
                        st.markdown(f"**Upload Date:** {info.get('upload_date', 'N/A')}")

                    if info.get('thumbnail'):
                        st.image(info['thumbnail'], caption="Video Thumbnail", width=300)
                else:
                    st.error("❌ Could not fetch video information. Please check the URL.")

        if url and show_formats:
            with st.spinner("Fetching available formats..."):
                formats = get_available_formats(url)

                if formats:
                    st.markdown("#### 🎛️ Available Formats")

                    # Show video formats
                    if formats['video_formats']:
                        st.markdown("**📹 Video Formats (video only):**")
                        for fmt in sorted(formats['video_formats'], key=lambda x: x.get('height', 0), reverse=True)[:10]:
                            quality_info = f"{fmt.get('height', '?')}p" if fmt.get('height') else "Unknown"
                            codec = fmt.get('vcodec', 'unknown')
                            if len(codec) > 15:
                                codec = codec[:12] + "..."
                            filesize = format_filesize(fmt.get('filesize'))
                            st.code(f"ID: {fmt.get('format_id')} | {quality_info} | {codec} | {filesize}")

                    # Show audio formats
                    if formats['audio_formats']:
                        st.markdown("**🎵 Audio Formats (audio only):**")
                        for fmt in sorted(formats['audio_formats'], key=lambda x: x.get('abr', 0), reverse=True)[:5]:
                            bitrate = f"{fmt.get('abr', '?')}kbps" if fmt.get('abr') else "Unknown"
                            codec = fmt.get('acodec', 'unknown')
                            filesize = format_filesize(fmt.get('filesize'))
                            st.code(f"ID: {fmt.get('format_id')} | {bitrate} | {codec} | {filesize}")

                    # Show recommended combinations
                    st.markdown("**🔗 Recommended Combinations:**")
                    st.info("💡 **Tip:** Use format IDs like `137+251` for 1080p video + best audio, or `136+140` for 720p + medium audio")

                else:
                    st.error("❌ Could not fetch format information.")

        if url and download_btn:
            # Show format being used
            if use_custom_format and custom_format_input:
                selected_format = custom_format_input
                st.info(f"🎯 **Using custom format:** `{selected_format}`")
            else:
                format_mappings = {
                    "Best Available": "bestvideo[height<=1080]+bestaudio/bestvideo*+bestaudio/best",
                    "4K": "bestvideo[height<=2160]+bestaudio/best[height<=2160]",
                    "1440p": "bestvideo[height<=1440]+bestaudio/best[height<=1440]",
                    "1080p": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
                    "720p": "bestvideo[height<=720]+bestaudio/best[height<=720]",
                    "480p": "bestvideo[height<=480]+bestaudio/best[height<=480]"
                }
                selected_format = format_mappings.get(quality, "bestvideo*+bestaudio/best")
                st.info(f"🎯 **Selected quality:** {quality} (`{selected_format}`)")
            options = create_download_options(
                quality=quality,
                audio_only=(download_mode == "Audio Only"),
                subtitle_langs=subtitle_langs,
                custom_format=custom_format_input if use_custom_format else None
            )

            # Add metadata options
            if embed_metadata or embed_thumbnail:
                if 'postprocessors' not in options:
                    options['postprocessors'] = []

                if embed_metadata:
                    options['postprocessors'].append({
                        'key': 'FFmpegMetadata'
                    })

                if embed_thumbnail:
                    options['postprocessors'].append({
                        'key': 'EmbedThumbnail'
                    })

            if write_thumbnail:
                options['writethumbnail'] = True

            progress_bar = st.progress(0)
            status_text = st.empty()

            status_text.text("Starting download...")
            progress_bar.progress(25)

            success, error = download_video(url, options)

            if success:
                progress_bar.progress(100)
                st.markdown("""
                <div class="success-box">
                    ✅ Download completed successfully!
                </div>
                """, unsafe_allow_html=True)

                # Add to history
                st.session_state.download_history.append({
                    'url': url,
                    'type': 'Single Video',
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
            else:
                st.markdown(f"""
                <div class="error-box">
                    ❌ Download failed: {error}
                </div>
                """, unsafe_allow_html=True)

    elif download_mode == "Playlist":
        st.markdown("### 📋 Playlist Download")

        playlist_url = st.text_input(
            "Enter Playlist URL:",
            placeholder="https://www.youtube.com/playlist?list=..."
        )

        if playlist_url and st.button("📋 Preview Playlist"):
            with st.spinner("Fetching playlist information..."):
                info = get_video_info(playlist_url)

                if info and 'entries' in info:
                    st.markdown(f"#### 📋 Playlist: {info.get('title', 'Unknown')}")
                    st.markdown(f"**Total Videos:** {len(info['entries'])}")

                    # Show first few videos
                    st.markdown("**First 5 videos:**")
                    for i, entry in enumerate(info['entries'][:5]):
                        if entry:
                            st.markdown(f"  {i+1}. {entry.get('title', 'Unknown')}")
                else:
                    st.error("❌ Could not fetch playlist information.")

        if playlist_url and st.button("⬬ Download Playlist", type="primary"):
            options = create_download_options(
                quality=quality,
                audio_only=(download_mode == "Audio Only"),
                subtitle_langs=subtitle_langs
            )
            options['noplaylist'] = False

            progress_bar = st.progress(0)
            status_text = st.empty()

            status_text.text("Downloading playlist...")
            progress_bar.progress(50)

            success, error = download_video(playlist_url, options)

            if success:
                progress_bar.progress(100)
                st.markdown("""
                <div class="success-box">
                    ✅ Playlist downloaded successfully!
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="error-box">
                    ❌ Playlist download failed: {error}
                </div>
                """, unsafe_allow_html=True)

    elif download_mode == "Audio Only":
        st.markdown("### 🎵 Audio Only Download")

        audio_url = st.text_input(
            "Enter Video URL:",
            placeholder="https://www.youtube.com/watch?v=..."
        )

        if audio_url and st.button("⬬ Download Audio", type="primary"):
            options = create_download_options(
                audio_only=True,
                subtitle_langs=None
            )

            progress_bar = st.progress(0)
            status_text = st.empty()

            status_text.text("Extracting audio...")
            progress_bar.progress(50)

            success, error = download_video(audio_url, options)

            if success:
                progress_bar.progress(100)
                st.markdown("""
                <div class="success-box">
                    🎵 Audio extracted successfully!
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="error-box">
                    ❌ Audio extraction failed: {error}
                </div>
                """, unsafe_allow_html=True)

    elif download_mode == "Batch URLs":
        st.markdown("### 📦 Batch Download")

        urls_text = st.text_area(
            "Enter URLs (one per line):",
            placeholder="https://www.youtube.com/watch?v=...\nhttps://www.youtube.com/watch?v=...",
            height=150
        )

        if urls_text and st.button("⬬ Download All", type="primary"):
            urls = [url.strip() for url in urls_text.split('\n') if url.strip()]

            if urls:
                options = create_download_options(
                    quality=quality,
                    audio_only=(download_mode == "Audio Only"),
                    subtitle_langs=subtitle_langs
                )

                progress_bar = st.progress(0)
                status_text = st.empty()

                successful = 0
                total = len(urls)

                for i, url in enumerate(urls):
                    status_text.text(f"Downloading {i+1}/{total}: {url[:50]}...")
                    progress_bar.progress((i + 1) / total)

                    success, error = download_video(url, options)
                    if success:
                        successful += 1

                    time.sleep(0.5)  # Small delay for UI updates

                if successful == total:
                    st.markdown(f"""
                    <div class="success-box">
                        ✅ All {total} downloads completed successfully!
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="info-box">
                        ℹ️ Completed {successful}/{total} downloads successfully.
                    </div>
                    """, unsafe_allow_html=True)

with col2:
    st.markdown("### 📊 Download Info")

    # Output directory info
    output_dir = get_output_directory()
    st.markdown(f"**📁 Output Directory:**")
    st.code(output_dir, language="text")

    # Check if ffmpeg is available
    ffmpeg_available = shutil.which("ffmpeg") is not None
    if ffmpeg_available:
        st.success("✅ FFmpeg is available")
    else:
        st.warning("⚠️ FFmpeg not found. Some features may not work.")

    # Download history
    if st.session_state.download_history:
        st.markdown("### 📈 Recent Downloads")
        for item in st.session_state.download_history[-5:]:
            st.markdown(f"**{item['type']}** - {item['timestamp']}")
            st.markdown(f"🔗 {item['url'][:30]}...")
            st.markdown("---")

    # Clear history button
    if st.session_state.download_history and st.button("🗑️ Clear History"):
        st.session_state.download_history = []
        st.rerun()

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 1rem;">
    <p>🎥 YouTube Downloader Pro | Made with ❤️ using Streamlit</p>
    <p><small>Use responsibly. Download only content you have rights to download.</small></p>
</div>
""", unsafe_allow_html=True)
