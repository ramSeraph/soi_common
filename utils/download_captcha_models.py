import os
import sys
import requests

def download_file(url, dest_path):
    """Downloads a file from a URL to a destination path."""
    print(f"Downloading {url} to {dest_path}")
    response = requests.get(url, stream=True)
    response.raise_for_status()
    with open(dest_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <models_dir>")
        sys.exit(1)

    models_folder = sys.argv[1]

    os.makedirs(models_folder, exist_ok=True)

    files_to_download = [
        'lstm_eng.traineddata',
        'lstm_osd.traineddata',
        'old_eng.traineddata',
        'old_myconfig'
    ]

    base_url = "https://github.com/ramSeraph/opendata/releases/download/tesseract-models/"

    for f in files_to_download:
        url = base_url + f
        dest_path = os.path.join(models_folder, f)
        download_file(url, dest_path)

    lstm_dir = os.path.join(models_folder, 'lstm')
    old_dir = os.path.join(models_folder, 'old')
    os.makedirs(lstm_dir, exist_ok=True)
    os.makedirs(old_dir, exist_ok=True)

    os.rename(os.path.join(models_folder, 'lstm_eng.traineddata'), os.path.join(lstm_dir, 'eng.traineddata'))
    os.rename(os.path.join(models_folder, 'lstm_osd.traineddata'), os.path.join(lstm_dir, 'osd.traineddata'))
    os.rename(os.path.join(models_folder, 'old_eng.traineddata'), os.path.join(old_dir, 'eng.traineddata'))
    os.rename(os.path.join(models_folder, 'old_myconfig'), os.path.join(old_dir, 'myconfig'))

    print("All models downloaded and moved successfully.")

if __name__ == "__main__":
    main()
