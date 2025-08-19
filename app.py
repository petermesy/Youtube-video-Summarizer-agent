import streamlit as st
from pytube import Search
from youtube_transcript_api import YouTubeTranscriptApi
import google.generativeai as genai
import yt_dlp
import re
import os

# 🔑 Set your Google API key (better: use .env file)
os.environ["GOOGLE_API_KEY"] = "AIzaSyA0a3ld-hCKxrsnTCYZA_aU8JJdENqhHSg"
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel('gemini-2.0-flash')

# Example: helper functions (replace with your full ones)
def fetch_transcript(video_id):
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        return " ".join([t["text"] for t in transcript])
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
    if topic and st.button("Generate Summaries"):
        st.info(f"Searching YouTube for: {topic}")
        search = Search(topic)
        results = search.results[:5]  # Get top 5 results
        if not results:
            st.warning("No videos found for this topic.")
            return
        for video in results:
            video_id = video.video_id
            title = video.title
            channel = video.author
            url = f"https://www.youtube.com/watch?v={video_id}"
            st.markdown(f"**[{title}]({url})**  ")
            st.caption(f"Channel: {channel}")
            # Fetch transcript and summarize
            transcript = fetch_transcript(video_id)
            if transcript:
                with st.expander("Show summary"):
                    summary = generate_summary(title, channel, transcript)
                    st.write(summary)
            else:
                st.warning("Transcript not available for this video.")

if __name__ == "__main__":
    main()
