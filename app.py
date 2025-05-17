from flask import Flask, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi
from googleapiclient.discovery import build
import os

app = Flask(__name__)

# 환경변수에서 API 키 읽기
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")
if not YOUTUBE_API_KEY:
    raise ValueError("YOUTUBE_API_KEY is not set in environment variables")

# 유튜브 API 클라이언트 생성
youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

def get_channel_id_from_url(channel_url):
    try:
        if "/channel/" in channel_url:
            return channel_url.split("/channel/")[1].split("/")[0]

        # @username 방식 처리
        elif "youtube.com/@" in channel_url:
            username = channel_url.split("youtube.com/@")[1].split("/")[0]
            search_response = youtube.search().list(
                part="snippet",
                q=username,
                type="channel",
                maxResults=1
            ).execute()

            if search_response["items"]:
                return search_response["items"][0]["snippet"]["channelId"]

    except Exception as e:
        print(f"[ERROR] 채널 ID 추출 실패: {e}")
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
        if not next_page_token or len(videos) >= 100:
            break

    return videos

@app.route("/")
def hello():
    return "Hello from transcript API!"

@app.route("/fetch_transcripts", methods=["POST"])
def fetch_transcripts():
    data = request.get_json()
    channel_url = data.get("channel_url")

    channel_id = get_channel_id_from_url(channel_url)
    print(f"[INFO] 채널 URL: {channel_url}")
    print(f"[INFO] 채널 ID: {channel_id}")

    if not channel_id:
        return jsonify({"error": "채널 ID를 찾을 수 없습니다."}), 400

    video_ids = get_video_ids_from_channel(channel_id)
    print(f"[INFO] 영상 수: {len(video_ids)}개")

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

    print(f"[INFO] 자막 수집 완료: {len(results)}개")
    return jsonify(results)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
