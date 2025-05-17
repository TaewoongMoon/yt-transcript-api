from flask import Flask, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi
from googleapiclient.discovery import build
import os
import logging

# -------------------------------
# 1. 로깅 & Flask 앱 선언
# -------------------------------
logging.basicConfig(level=logging.INFO)
app = Flask(__name__)

# -------------------------------
# 2. YouTube API 키 및 클라이언트 설정
# -------------------------------
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")
if not YOUTUBE_API_KEY:
    raise ValueError("YOUTUBE_API_KEY is not set in environment variables")

youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

# -------------------------------
# 3. 채널 URL → 채널 ID 추출
# -------------------------------
def get_channel_id_from_url(channel_url):
    try:
        if "/channel/" in channel_url:
            return channel_url.split("/channel/")[1].split("/")[0]
        elif "youtube.com/@" in channel_url:
            username = channel_url.split("youtube.com/@")[1].split("/")[0]
            res = youtube.search().list(
                part="snippet",
                q=username,
                type="channel",
                maxResults=1
            ).execute()
            if res["items"]:
                return res["items"][0]["snippet"]["channelId"]
    except Exception as e:
        logging.error(f"[ERROR] 채널 ID 추출 실패: {e}")
    return None

# -------------------------------
# 4. 채널 ID → 영상 ID 목록 추출
# -------------------------------
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

# -------------------------------
# 5. 기본 라우트 (서버 확인용)
# -------------------------------
@app.route("/")
def hello():
    return "Hello from transcript API!"

# -------------------------------
# 6. 핵심 기능 라우트: 자막 수집
# -------------------------------
@app.route("/fetch_transcripts", methods=["POST"])
def fetch_transcripts():
    data = request.get_json()
    channel_url = data.get("channel_url")

    logging.info(f"요청받은 채널 URL: {channel_url}")
    channel_id = get_channel_id_from_url(channel_url)
    logging.info(f"채널 ID: {channel_id}")

    if not channel_id:
        return jsonify({"error": "채널 ID를 찾을 수 없습니다."}), 400

    video_ids = get_video_ids_from_channel(channel_id)
    logging.info(f"총 영상 수: {len(video_ids)}개")

    results = []
    for vid in video_ids:
        try:
            transcript = YouTubeTranscriptApi.get_transcript(vid, languages=["ko", "en"])
            text = " ".join([t["text"] for t in transcript])
            results.append({
                "video_url": f"https://youtu.be/{vid}",
                "transcript": text
            })
        except Exception as e:
            logging.warning(f"자막 수집 실패 (영상: {vid}): {e}")
            continue

    logging.info(f"자막 수집 완료: {len(results)}개")
    return jsonify(results)

# -------------------------------
# 7. 서버 실행 (Render 환경 변수 사용)
# -------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
