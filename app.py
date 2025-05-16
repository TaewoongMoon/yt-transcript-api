# app.py
from flask import Flask, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi
import requests, re

app = Flask(__name__)

def get_video_ids(channel_url):
    html = requests.get(channel_url + "/videos").text
    return list(set(re.findall(r"watch\?v=([a-zA-Z0-9_-]{11})", html)))

@app.route("/")
def hello():
    return "Hello from transcript API!"

@app.route("/fetch_transcripts", methods=["POST"])
def fetch_transcripts():
    channel_url = request.json.get("channel_url")
    video_ids = get_video_ids(channel_url)
    results = []
    for vid in video_ids[:10]:
        try:
            transcript = YouTubeTranscriptApi.get_transcript(vid, languages=["ko", "en"])
            text = " ".join([t["text"] for t in transcript])
            results.append({"video_url": f"https://youtu.be/{vid}", "transcript": text})
        except:
            continue
    return jsonify(results)
