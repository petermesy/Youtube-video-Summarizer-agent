
import streamlit as st
from pytube import Search
from youtube_transcript_api import YouTubeTranscriptApi
import google.generativeai as genai
import yt_dlp
import re
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# 🔑 Set your Google API key from .env
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel('gemini-2.0-flash')

# Example: helper functions (replace with your full ones)
def fetch_transcript(video_id):
    # Try YouTubeTranscriptApi first
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        return " ".join([t["text"] for t in transcript])
    except Exception:
        pass
    # Fallback: try yt-dlp to get subtitles (auto-generated or manual)
    try:
        url = f"https://www.youtube.com/watch?v={video_id}"
        ydl_opts = {
            'skip_download': True,
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitlesformat': 'vtt',
            'quiet': True,
            'forcejson': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            subs = info.get('subtitles') or info.get('automatic_captions')
            if not subs:
                return None
            # Prefer Amharic, then English, then any
            for lang in ['am', 'en'] + list(subs.keys()):
                if lang in subs:
                    sub_url = subs[lang][0]['url']
                    import requests
                    vtt = requests.get(sub_url).text
                    # Convert VTT to plain text
                    lines = [line for line in vtt.splitlines() if line and not line.startswith(('WEBVTT', 'X-TIMESTAMP', 'NOTE')) and not re.match(r'\d{2}:\d{2}:\d{2}\.\d{3}', line)]
                    return ' '.join(lines)
        return None
    except Exception:
        return None

def generate_summary(title, channel, transcript):
    response = model.generate_content(
        f"Summarize this YouTube video titled '{title}' from {channel}:\n\n{transcript}"
    )
    return response.text

def main():
    st.set_page_config(page_title="YouTube Summarizer", layout="wide")
    st.title("🎬 YouTube Video Summarizer")

    topic = st.text_input("🔍 Search topic", placeholder="e.g., 'python tutorials'")
    if topic:
        summarize_all = st.checkbox("Summarize all videos into one combined summary")
        if st.button("Generate Summaries"):
            st.info(f"Searching YouTube for: {topic}")
            search = Search(topic)
            results = search.results[:5]  # Get top 5 results
            if not results:
                st.warning("No videos found for this topic.")
                return
            video_summaries = []
            for video in results:
                video_id = video.video_id
                title = video.title
                channel = video.author
                url = f"https://www.youtube.com/watch?v={video_id}"
                st.markdown(f"**[{title}]({url})**  ")
                st.caption(f"Channel: {channel}")
                transcript = fetch_transcript(video_id)
                if transcript:
                    summary = generate_summary(title, channel, transcript)
                    video_summaries.append(f"Video: {title} (Channel: {channel})\nSummary: {summary}")
                    with st.expander("Show summary"):
                        st.write(summary)
                else:
                    st.warning("Transcript not available for this video.")
            if summarize_all and video_summaries:
                st.subheader("Combined Summary of All Videos")
                combined_input = "\n\n".join(video_summaries)
                combined_summary = model.generate_content(
                    f"Summarize the following summaries of YouTube videos about '{topic}':\n\n{combined_input}"
                ).text
                st.success(combined_summary)

if __name__ == "__main__":
    main()
