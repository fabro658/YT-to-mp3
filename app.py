from flask import Flask, render_template, request
import yt_dlp
import os

app = Flask(__name__)

DOWNLOAD_DIR = os.path.expanduser("~/Downloads")

def download_video(url, format_type):
    if format_type == "mp3":
        options = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
    else:  # mp4
        options = {
            'format': 'mp4',
            'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),
        }

    with yt_dlp.YoutubeDL(options) as ydl:
        ydl.download([url])

@app.route("/", methods=["GET", "POST"])
def index():
    message = ""
    if request.method == "POST":
        url = request.form.get("playlist_url")
        format_type = request.form.get("format")
        try:
            download_video(url, format_type)
            message = f"Téléchargement réussi en {format_type.upper()} !"
        except Exception as e:
            message = f"Erreur : {str(e)}"
    return render_template("index.html", message=message)

if __name__ == "__main__":
    app.run(debug=True)
