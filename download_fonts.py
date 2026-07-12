import os
import urllib.request

FONTS_DIR = os.path.join(os.path.dirname(__file__), "fonts")
os.makedirs(FONTS_DIR, exist_ok=True)

FONT_URLS = {
    "CourierPrime.ttf": "https://github.com/google/fonts/raw/main/ofl/courierprime/CourierPrime-Regular.ttf",
    "CourierPrime-Bold.ttf": "https://github.com/google/fonts/raw/main/ofl/courierprime/CourierPrime-Bold.ttf"
}

def download_fonts():
    for filename, url in FONT_URLS.items():
        dest = os.path.join(FONTS_DIR, filename)
        if not os.path.exists(dest):
            print(f"Downloading {filename} from {url}...")
            try:
                urllib.request.urlretrieve(url, dest)
                print(f"Successfully downloaded {filename} to {dest}")
            except Exception as e:
                print(f"Error downloading {filename}: {e}")
        else:
            print(f"{filename} already exists at {dest}")

if __name__ == "__main__":
    download_fonts()
