from flask import Flask, render_template, request, send_file
import subprocess
import os
import re
import shutil
import tempfile
import zipfile

app = Flask(__name__)

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
        return name or "playlist"
    except subprocess.CalledProcessError:
        return "playlist"

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        url = request.form.get("playlist_url")
        if url:
            playlist_name = extract_playlist_name(url)

            with tempfile.TemporaryDirectory() as temp_dir:
                output_path = os.path.join(temp_dir, "%(playlist_index)s - %(title)s.%(ext)s")

                command = [
                    "yt-dlp",
                    "-x",
                    "--audio-format", "mp3",
                    "-o", output_path,
                    url
                ]

                try:
                    subprocess.run(command, cwd=temp_dir, check=True)
                except subprocess.CalledProcessError:
                    return render_template("index.html", message="Erreur pendant le téléchargement.")

                # Création de l'archive zip
                zip_path = os.path.join(temp_dir, f"{playlist_name}.zip")
                with zipfile.ZipFile(zip_path, 'w') as zipf:
                    for root, dirs, files in os.walk(temp_dir):
                        for file in files:
                            if file.endswith(".mp3"):
                                file_path = os.path.join(root, file)
                                arcname = os.path.relpath(file_path, temp_dir)
                                zipf.write(file_path, arcname)

                return send_file(zip_path,
                                 mimetype='application/zip',
                                 as_attachment=True,
                                 download_name=f"{playlist_name}.zip")

    return render_template("index.html", message="")

if __name__ == "__main__":
    app.run(debug=True)