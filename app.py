from flask import Flask, render_template, request
import subprocess
import os
import re

app = Flask(__name__, static_url_path="/static")
BASE_DOWNLOAD_DIR = os.path.join("static", "downloads")
os.makedirs(BASE_DOWNLOAD_DIR, exist_ok=True)

def extract_playlist_name(url):
    """
    Utilise yt-dlp pour obtenir le nom de la playlist.
    """
    try:
        result = subprocess.run(
            ["yt-dlp", "--print", "%(playlist_title)s", url],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        name = result.stdout.strip()
        name = re.sub(r'[^\w\s-]', '', name).strip().replace(' ', '_')
        return name if name else "playlist_inconnue"
    except subprocess.CalledProcessError:
        return "playlist_inconnue"

@app.route("/", methods=["GET", "POST"])
def index():
    message = ""
    files = []
    
    if request.method == "POST":
        url = request.form.get("playlist_url")
        if url:
            playlist_name = extract_playlist_name(url)
            target_dir = os.path.join(BASE_DOWNLOAD_DIR, playlist_name)
            os.makedirs(target_dir, exist_ok=True)

            output_template = os.path.join(target_dir, "%(playlist_index)s - %(title)s.%(ext)s")
            command = [
                "yt-dlp",
                "-x",
                "--audio-format", "mp3",
                "-o", output_template,
                url
            ]
            try:
                subprocess.run(command, check=True)
                message = f"Téléchargement terminé dans le dossier : {playlist_name}"
                for filename in os.listdir(target_dir):
                    file_path = os.path.join("static", "downloads", playlist_name, filename)
                    files.append("/" + file_path)
            except subprocess.CalledProcessError:
                message = "Erreur pendant le téléchargement."

    return render_template("index.html", message=message, files=files)

if __name__ == "__main__":
    app.run(debug=True)