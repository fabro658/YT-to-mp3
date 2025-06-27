from flask import Flask, render_template, request, send_from_directory, url_for
import subprocess
import os
import re

app = Flask(__name__)
BASE_DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), "downloads")
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
        # Nettoie le nom pour qu'il soit un nom de dossier valide
        name = re.sub(r'[^\w\s-]', '', name).strip().replace(' ', '_')
        return name
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

            command = [
                "yt-dlp",
                "-x",
                "--audio-format", "mp3",
                "-o", "%(playlist_index)s - %(title)s.%(ext)s",
                url
            ]
            try:
                subprocess.run(command, cwd=target_dir, check=True)
                message = f"Téléchargement terminé dans le dossier : {playlist_name}"

                # Récupère les fichiers mp3 générés
                for file in os.listdir(target_dir):
                    if file.endswith(".mp3"):
                        download_url = url_for('download_file', playlist=playlist_name, filename=file)
                        files.append({"name": file, "url": download_url})

            except subprocess.CalledProcessError:
                message = "Erreur pendant le téléchargement."

    return render_template("index.html", message=message, files=files)

@app.route('/downloads/<playlist>/<filename>')
def download_file(playlist, filename):
    """
    Sert un fichier mp3 à partir du dossier de téléchargement.
    """
    return send_from_directory(os.path.join(BASE_DOWNLOAD_DIR, playlist), filename, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
