import os
import re
import subprocess
import unicodedata
from flask import Flask, request, render_template

app = Flask(__name__)

# Chemin de base où toutes les playlists seront enregistrées
BASE_DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), "downloads")
os.makedirs(BASE_DOWNLOAD_DIR, exist_ok=True)

def sanitize_filename(name):
    """
    Nettoie un nom pour en faire un nom de dossier/fichier valide.
    """
    name = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode('ascii')
    name = re.sub(r'[^\w\-_.]', '_', name)
    return name.strip().replace('\n', '').replace('\r', '')

def extract_playlist_name(url):
    """
    Utilise yt-dlp pour extraire le titre de la playlist.
    """
    try:
        result = subprocess.run(
            ["yt-dlp", "--print", "%(playlist_title)s", url],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        raw_name = result.stdout.strip()
        return sanitize_filename(raw_name)
    except subprocess.CalledProcessError:
        return "playlist_inconnue"

@app.route("/", methods=["GET", "POST"])
def index():
    message = ""
    if request.method == "POST":
        url = request.form.get("playlist_url")
        if url:
            playlist_name = extract_playlist_name(url)
            target_dir = os.path.join(BASE_DOWNLOAD_DIR, playlist_name)
            os.makedirs(target_dir, exist_ok=True)

            command = [
                "yt-dlp",
                "-x",
                "--audio-format", "mp3",
                "-o", "%(playlist_index)s - %(title)s.%(ext)s",
                url
            ]

            try:
                # 4. Lance le téléchargement dans ce dossier
                subprocess.run(command, cwd=target_dir, check=True)
                message = f" Playlist téléchargée dans le dossier : <b>{playlist_name}</b>"
            except subprocess.CalledProcessError:
                message = " Erreur pendant le téléchargement."

    return render_template("index.html", message=message)

if __name__ == "__main__":
    app.run(debug=True)