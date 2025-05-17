import logging
logging.basicConfig(level=logging.INFO)

...

@app.route("/fetch_transcripts", methods=["POST"])
def fetch_transcripts():
    data = request.get_json()
    channel_url = data.get("channel_url")

    channel_id = get_channel_id_from_url(channel_url)
    logging.info(f"채널 URL: {channel_url}")
    logging.info(f"채널 ID: {channel_id}")

    if not channel_id:
        return jsonify({"error": "채널 ID를 찾을 수 없습니다."}), 400

    video_ids = get_video_ids_from_channel(channel_id)
    logging.info(f"영상 수: {len(video_ids)}개")

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

    logging.info(f"자막 수집 완료: {len(results)}개")
    return jsonify(results)
