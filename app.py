# Required imports for all tools
import streamlit as st
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
import google.generativeai as genai
import os
from dotenv import load_dotenv


# --- Tool 1: Load environment variables and configure models ---
load_dotenv()
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')

# --- Tool 2: YouTube Search Tool ---
def youtube_search(query, max_results=5):
    youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
    request = youtube.search().list(
        q=query, part="id,snippet", type="video", maxResults=max_results
    )
    response = request.execute()
    results = []
    for item in response.get("items", []):
        video_id = item["id"]["videoId"]
        title = item["snippet"]["title"]
        channel = item["snippet"]["channelTitle"]
        results.append({"video_id": video_id, "title": title, "channel": channel})
    return results

# --- Tool 3: Transcript Fetch Tool ---
def fetch_transcript(video_id):
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        return " ".join([t["text"] for t in transcript])
    except Exception:
        return None

# --- Tool 4: Summarization Tool ---
def summarize(title, channel, transcript):
    if not transcript:
        return None
    response = model.generate_content(
        f"Summarize this YouTube video titled '{title}' from {channel}:\n\n{transcript}"
    )
    return response.text

# --- Tool 5: Combined Summary Tool (optional) ---
def summarize_all(videos):
    combined_input = "\n\n".join(
        [f"Video: {v['title']} (Channel: {v['channel']})\nSummary: {v['summary']}" for v in videos if v.get('summary')]
    )
    if not combined_input:
        return None
    response = model.generate_content(
        f"Summarize the following summaries of YouTube videos:\n\n{combined_input}"
    )
    return response.text

def main():
    st.set_page_config(page_title="YouTube Summarizer", layout="wide")
    st.title("YouTube Topic Summarizer (Manual Tool-Calling Agent)")
    topic = st.text_input("Enter a topic to search on YouTube:")
    if st.button("Search and Summarize") and topic:
        st.info(f"Searching YouTube for: {topic}")
        videos = youtube_search(topic)
        if not videos:
            st.warning("No videos found for this topic.")
            return
        for v in videos:
            st.markdown(f"**[{v['title']}](https://www.youtube.com/watch?v={v['video_id']})**")
            st.caption(f"Channel: {v['channel']}")
            transcript = fetch_transcript(v['video_id'])
            summary = summarize(v['title'], v['channel'], transcript)
            if summary:
                with st.expander("Show summary"):
                    st.write(summary)
            else:
                st.warning("Transcript not available for this video.")

if __name__ == "__main__":
    main()
