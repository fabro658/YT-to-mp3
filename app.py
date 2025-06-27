from flask import Flask, render_template, request, send_file
import subprocess
import os
import re
import shutil
import zipfile
import unicodedata

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
        # Nettoie pour que ce soit un nom de dossier valide
        return sanitize_filename(name)
    except subprocess.CalledProcessError:
        return "playlist_inconnue"

def sanitize_filename(name):
    """
    Nettoie un nom de fichier en supprimant les caractères invalides.
    """
    name = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode('ascii')
    name = re.sub(r'[^\w\-_.]', '_', name)
    return name.strip().replace('\n', '').replace('\r', '')

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

                # Créer un fichier ZIP de la playlist téléchargée
                zip_path = os.path.join(BASE_DOWNLOAD_DIR, f"{playlist_name}.zip")
                with zipfile.ZipFile(zip_path, "w") as zipf:
                    for root, _, files in os.walk(target_dir):
                        for file in files:
                            full_path = os.path.join(root, file)
                            arcname = os.path.relpath(full_path, start=target_dir)
                            zipf.write(full_path, arcname=arcname)

                # Optionnel : supprimer le dossier temporaire une fois zippé
                shutil.rmtree(target_dir)

                # Envoie le ZIP au navigateur
                return send_file(
                    zip_path,
                    as_attachment=True,
                    download_name=f"{playlist_name}.zip",
                    mimetype='application/zip'
                )

            except subprocess.CalledProcessError:
                message = "Erreur pendant le téléchargement."

            except Exception as e:
                message = f"Erreur serveur : {e}"

    return render_template("index.html", message=message)

if __name__ == "__main__":
    app.run(debug=True)
