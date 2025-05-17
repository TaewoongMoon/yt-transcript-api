from flask import Flask, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi
from googleapiclient.discovery import build
import requests
import re
import os

app = Flask(__name__)

# YouTube API 키 환경변수에서 가져오기
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")
youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

def get_channel_id_from_url(channel_url):
    if "@THE_freezia" in channel_url:
        # 사용자명 기반 채널
        username = channel_url.split("@")[1]
        res = youtube.channels().list(forUsername=username, part='id').execute()
        if res["items"]:
            return res["items"][0]["id"]
    elif "/channel/" in channel_url:
        # 채널 ID 직접 포함된 경우
        return channel_url.split("/channel/")[1].split("/")[0]
    else:
        # fallback (HTML에서 추출 시도, 비추천)
        return None

def get_video_ids_from_channel(channel_id):
    videos = []
    next_page_token = None

    while True:
        res = youtube.search().list(
            part="id",
            channelId=channel_id,
            maxResults=50,
            pageToken=next_page_token,
            type="video"
        ).execute()

        for item in res["items"]:
            videos.append(item["id"]["videoId"])

        next_page_token = res.get("nextPageToken")
        if not next_page_token or len(videos) > 100:
            break

    return videos

@app.route("/")
def hello():
    return "Hello from transcript API!"

@app.route("/fetch_transcripts", methods=["POST"])
def fetch_transcripts():
    channel_url = request.json.get("channel_url")
    channel_id = get_channel_id_from_url(channel_url)

    if not channel_id:
        return jsonify({"error": "Invalid channel URL"}), 400

    video_ids = get_video_ids_from_channel(channel_id)
    results = []

    for vid in video_ids:
        try:
            transcript = YouTubeTranscriptApi.get_transcript(vid, languages=["ko", "en"])
            text = " ".join([t["text"] for t in transcript])
            results.append({
                "video_url": f"https://youtu.be/{vid}",
                "transcript": text
            })
        except:
            continue

    return jsonify(results)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
