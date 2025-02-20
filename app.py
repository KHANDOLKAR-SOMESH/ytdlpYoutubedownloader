from flask import Flask, render_template, request, send_file
import yt_dlp
import subprocess
import os
import uuid
import time

app = Flask(__name__)

TEMP_FOLDER = "temp_downloads"
os.makedirs(TEMP_FOLDER, exist_ok=True)

# Automatically clean up temp files after 5 minutes
def cleanup_old_files():
    now = time.time()
    for filename in os.listdir(TEMP_FOLDER):
        file_path = os.path.join(TEMP_FOLDER, filename)
        if os.path.isfile(file_path) and now - os.path.getmtime(file_path) > 300:  # 5 min
            os.remove(file_path)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        url = request.form.get("url")
        if not url:
            return render_template("index.html", error="No URL provided")

        try:
            ydl_opts = {"quiet": True, "noplaylist": True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

            video_id = info.get("id")
            thumbnail_url = f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"

            video_formats = [
                {"resolution": fmt.get("height", "Unknown"), "url": fmt["url"]}
                for fmt in info["formats"]
                if fmt.get("ext") in ["mp4", "webm"] and fmt.get("vcodec") != "none" and fmt.get("acodec") == "none"
            ]

            audio_formats = [
                {"audio_bitrate": fmt.get("abr", "Unknown"), "url": fmt["url"]}
                for fmt in info["formats"]
                if fmt.get("acodec") != "none" and fmt.get("vcodec") == "none"
            ]

            return render_template(
                "index.html",
                title=info["title"],
                thumbnail_url=thumbnail_url,
                video_formats=video_formats,
                audio_formats=audio_formats,
                url=url
            )

        except Exception as e:
            return render_template("index.html", error=str(e))

    return render_template("index.html")

@app.route("/merge", methods=["GET"])
def merge():
    """ Merges selected video and audio and provides a download link. """
    video_url = request.args.get("video")
    audio_url = request.args.get("audio")

    if not video_url or not audio_url:
        return "Invalid request", 400

    unique_filename = f"{uuid.uuid4()}.mp4"
    output_path = os.path.join(TEMP_FOLDER, unique_filename)

    ffmpeg_cmd = [
        "ffmpeg", "-i", video_url, "-i", audio_url,
        "-c:v", "copy", "-c:a", "aac", "-strict", "experimental",
        "-y", output_path
    ]

    subprocess.run(ffmpeg_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    cleanup_old_files()  # Clean old temp files

    return send_file(output_path, as_attachment=True, download_name="video.mp4")

if __name__ == "__main__":
    app.run(debug=True, port=5000)
