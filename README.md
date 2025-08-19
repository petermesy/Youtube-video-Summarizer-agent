title: Next Ai
emoji: 💬
colorFrom: yellow
colorTo: purple
sdk: gradio
sdk_version: 5.0.1
app_file: app.py
pinned: false
license: mit
short_description: the revolution of ai

An example chatbot using [Gradio](https://gradio.app), [`huggingface_hub`](https://huggingface.co/docs/huggingface_hub/v0.22.2/en/index), and the [Hugging Face Inference API](https://huggingface.co/docs/api-inference/index).
# YouTube Topic Summarizer

A simple Streamlit app that searches YouTube for videos on a user-given topic, fetches their transcripts, and summarizes them using Google's Gemini LLM.

## Features
- Search YouTube for any topic
- Display top 5 relevant videos (title, channel, link)
- Fetch video transcripts (if available)
- Summarize each video using Gemini LLM

## Requirements
- Python 3.8+
- Streamlit
- pytube
- youtube-transcript-api
- google-generativeai
- yt-dlp

## Setup
1. Clone or download this repository.
2. Install dependencies:
	```sh
	pip install -r requirements.txt
	```
3. Set your Google API key in your environment variables or directly in `app.py` (for Gemini access).

## Usage
Run the Streamlit app:
```sh
streamlit run app.py
```

Enter a topic in the search box and click "Generate Summaries". The app will show the top 5 YouTube videos, fetch their transcripts, and display AI-generated summaries.

## Notes
- Some videos may not have transcripts available.
- Summarization uses Gemini LLM via the Google Generative AI API.

## License
MIT License"# Youtube-video-Summarizer-agent" 
