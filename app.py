from flask import Flask, render_template, request, send_file
import subprocess
import os
import re
import zipfile
import tempfile

app = Flask(__name__)
BASE_DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), "downloads")
os.makedirs(BASE_DOWNLOAD_DIR, exist_ok=True)

def extract_playlist_name(url):
    try:
        result = subprocess.run(
            ["yt-dlp", "--print", "%(playlist_title)s", url],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        name = result.stdout.strip()
        name = re.sub(r'[^\w\-_.]', '_', name)
        return name
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
                subprocess.run(command, cwd=target_dir, check=True)

                # Crée un ZIP temporaire
                temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
                with zipfile.ZipFile(temp_zip.name, 'w') as zipf:
                    for root, dirs, files in os.walk(target_dir):
                        for file in files:
                            full_path = os.path.join(root, file)
                            zipf.write(full_path, arcname=file)

                return send_file(
                    temp_zip.name,
                    as_attachment=True,
                    download_name=f"{playlist_name}.zip",  # Sûr maintenant
                    mimetype="application/zip"
                )

            except subprocess.CalledProcessError:
                message = "Erreur pendant le téléchargement."

    return render_template("index.html", message=message)

if __name__ == "__main__":
    app.run(debug=True)
