from flask import Flask, request, send_file, render_template_string
import subprocess
import os
import re
import shutil
import zipfile
import unicodedata
import tempfile

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
        return sanitize_filename(name)
    except subprocess.CalledProcessError as e:
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
            temp_dir = tempfile.mkdtemp()
            target_dir = os.path.join(temp_dir, playlist_name)
            os.makedirs(target_dir, exist_ok=True)

            command = [
                "yt-dlp",
                "-x", "--audio-format", "mp3",
                "-o", "%(playlist_index)s - %(title)s.%(ext)s",
                url
            ]

            try:
                result = subprocess.run(
                    command,
                    cwd=target_dir,
                    check=True,
                    stderr=subprocess.PIPE,
                    text=True
                )

                # Crée un fichier ZIP
                zip_path = os.path.join(temp_dir, f"{playlist_name}.zip")
                with zipfile.ZipFile(zip_path, "w") as zipf:
                    for root, _, files in os.walk(target_dir):
                        for file in files:
                            full_path = os.path.join(root, file)
                            arcname = os.path.relpath(full_path, start=target_dir)
                            zipf.write(full_path, arcname=arcname)

                shutil.rmtree(target_dir)

                return send_file(
                    zip_path,
                    as_attachment=True,
                    download_name=f"{playlist_name}.zip",
                    mimetype='application/zip'
                )

            except subprocess.CalledProcessError as e:
                message = f"Erreur yt-dlp :<br><pre>{e.stderr}</pre>"

            except Exception as e:
                message = f"Erreur serveur :<br><pre>{str(e)}</pre>"

    return render_template_string("""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
      <meta charset="UTF-8">
      <title>Télécharger une playlist</title>
    </head>
    <body style="font-family:sans-serif; display:flex; justify-content:center; align-items:center; height:100vh; background:#f0f0f0;">
      <form method="POST" style="background:#fff; padding:2rem; border-radius:8px; box-shadow:0 0 10px rgba(0,0,0,0.1); width:100%; max-width:500px;">
        <h2 style="margin-bottom:1rem;">Télécharger une playlist YouTube en MP3</h2>
        <input type="text" name="playlist_url" placeholder="URL de la playlist" required style="width:100%; padding:0.5rem; margin-bottom:1rem;">
        <button type="submit" style="padding:0.5rem 1rem;">Convertir et Télécharger</button>
        {% if message %}
          <div style="margin-top:1rem; color:red;">{{ message|safe }}</div>
        {% endif %}
      </form>
    </body>
    </html>
    """, message=message)

if __name__ == "__main__":
    app.run(debug=True)
