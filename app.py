from flask import Flask, render_template, request, send_file
import subprocess
import os
import re
import shutil
import tempfile

app = Flask(__name__)

def extract_playlist_name(url):
    """
    Utilise yt-dlp pour obtenir le nom de la playlist proprement.
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
        return name if name else "playlist"
    except subprocess.CalledProcessError:
        return "playlist"

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        url = request.form.get("playlist_url")
        if url:
            playlist_name = extract_playlist_name(url)

            # Créer un dossier temporaire
            with tempfile.TemporaryDirectory() as temp_dir:
                download_dir = os.path.join(temp_dir, playlist_name)
                os.makedirs(download_dir, exist_ok=True)

                command = [
                    "yt-dlp",
                    "-x",
                    "--audio-format", "mp3",
                    "-o", "%(playlist_index)s - %(title)s.%(ext)s",
                    url
                ]

                try:
                    subprocess.run(command, cwd=download_dir, check=True)

                    # Créer l'archive ZIP
                    zip_path = shutil.make_archive(
                        os.path.join(temp_dir, playlist_name), 
                        'zip', 
                        root_dir=download_dir
                    )

                    # Retourner le fichier ZIP directement au navigateur
                    return send_file(
                        zip_path,
                        as_attachment=True,
                        download_name=f"{playlist_name}.zip"
                    )

                except subprocess.CalledProcessError as e:
                    return render_template("index.html", message="Erreur pendant le téléchargement.")
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
