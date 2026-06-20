#!/usr/bin/env python3
from flask import Flask, render_template, request, jsonify, Response
import threading
import queue
import json
import os
import yt_dlp

app = Flask(__name__)

# 계정별 다운로드 진행상황 저장
progress_queues: dict[str, queue.Queue] = {}
download_status: dict[str, dict] = {}


def download_user_videos(username: str, count: int, output_dir: str, q: queue.Queue):
    downloaded = 0

    class ProgressHook:
        def __call__(self, d):
            nonlocal downloaded
            if d["status"] == "finished":
                downloaded += 1
                q.put({"type": "progress", "user": username, "count": downloaded, "total": count,
                       "filename": os.path.basename(d["filename"])})

    opts = {
        "outtmpl": os.path.join(output_dir, username, "%(id)s.%(ext)s"),
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "merge_output_format": "mp4",
        "quiet": True,
        "no_warnings": True,
        "playlistend": count,
        "retries": 5,
        "sleep_interval": 2,
        "progress_hooks": [ProgressHook()],
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        },
    }

    os.makedirs(os.path.join(output_dir, username), exist_ok=True)
    url = f"https://www.tiktok.com/@{username}"

    try:
        q.put({"type": "start", "user": username})
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])
        q.put({"type": "done", "user": username, "count": downloaded})
    except Exception as e:
        q.put({"type": "error", "user": username, "message": str(e)})


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/start", methods=["POST"])
def start():
    data = request.json
    def parse_username(u):
        u = u.strip()
        # URL 형식이면 계정명만 추출: https://www.tiktok.com/@username
        if "tiktok.com" in u:
            u = u.rstrip("/").split("@")[-1].split("?")[0]
        return u.lstrip("@")

    usernames = [parse_username(u) for u in data.get("users", []) if u.strip()]
    count = int(data.get("count", 100))
    output_dir = data.get("output_dir", "downloads")

    if not usernames:
        return jsonify({"error": "계정명을 입력해주세요"}), 400

    session_id = str(id(usernames))
    q = queue.Queue()
    progress_queues[session_id] = q
    download_status[session_id] = {"users": usernames, "total": count, "output_dir": output_dir}

    def run_all():
        threads = []
        for username in usernames:
            t = threading.Thread(target=download_user_videos, args=(username, count, output_dir, q), daemon=True)
            t.start()
            threads.append(t)
        for t in threads:
            t.join()
        q.put({"type": "all_done"})

    threading.Thread(target=run_all, daemon=True).start()
    return jsonify({"session_id": session_id})


@app.route("/stream/<session_id>")
def stream(session_id):
    q = progress_queues.get(session_id)
    if not q:
        return jsonify({"error": "세션 없음"}), 404

    def generate():
        while True:
            try:
                msg = q.get(timeout=60)
                yield f"data: {json.dumps(msg, ensure_ascii=False)}\n\n"
                if msg.get("type") == "all_done":
                    break
            except queue.Empty:
                yield "data: {\"type\": \"ping\"}\n\n"

    return Response(generate(), mimetype="text/event-stream")


if __name__ == "__main__":
    app.run(debug=True, port=5000, threaded=True)
