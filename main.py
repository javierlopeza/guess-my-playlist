import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import re
import textwrap
import requests
from io import BytesIO
from dotenv import load_dotenv
import os

# Load environment variables from the .env file
load_dotenv()

# Access the variables
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')

sp = spotipy.Spotify(
    auth_manager=SpotifyClientCredentials(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
    ),
)
    
playlists_urls = [
    # "https://open.spotify.com/playlist/0uKRWiIn2hwajx0uvg3uaB",
    # "https://open.spotify.com/playlist/0ZKB6ILjyJLTHBL7b4hwRi",
    # "https://open.spotify.com/playlist/2WQxrq5bmHMlVuzvtwwywV",
    # "https://open.spotify.com/playlist/0zYAWMkX0Ndv3irnKRi87o?si=a935dcc702ad41c1",
    # "https://open.spotify.com/playlist/59nfpMnawckRPRbvXZyIis?si=dadd648a90b948eb",
    # "https://open.spotify.com/playlist/3Z69yzU4PrK862RmbNJpde?si=4d8a014e596a4127",
    # "https://open.spotify.com/playlist/2RhOcodie2dtAqhNzFxK7T?si=c6f8fa74084e4512",
    # "https://open.spotify.com/playlist/6MT94Zb8vtaJ5bPJ3lYxxL?si=b4f49116715647bb",
    # "https://open.spotify.com/playlist/1caJNgl3pOBxKSRMIfFqvq?si=b79194d4eeb3436c",
    # "https://open.spotify.com/playlist/6WJi8nrrtCy7TZS9mfBnVP?si=8b9986ee4fa34fe4",
    # "https://open.spotify.com/playlist/5HbKCz3bYjsTdctDca33pG?si=f23a7db95b3b4800",
    "https://open.spotify.com/playlist/1cRkRJu4NMVRfKPV389Ksb?si=a51a2cc68ac54925",
]

for playlist_url in playlists_urls:

    playlist_id = playlist_url.split("/")[-1].split("?")[0]
    playlist_data = sp.playlist(playlist_id)

    # Print playlist name and total tracks
    print(f"Playlist Name: {playlist_data['name']}")
    print(f"Total Tracks: {playlist_data['tracks']['total']}")
    print()

    cards = []
    offset = 0
    while True:
        playlist_items = sp.playlist_items(playlist_id, offset=offset)["items"]
        if not playlist_items:
            break
        for item in playlist_items:
            track = item["track"]
            card = {
                "song": track["name"],
                "artists": ", ".join([a["name"] for a in track["artists"]]),
                "year": re.match(r"\d{4}", track["album"]["release_date"]).group(),
                "url": track["external_urls"]["spotify"],
                "bg_url": sorted(track["album"]["images"], key=lambda x: -x["width"])[0]["url"],
            }
            cards.append(card)
            print(card)
        offset += 100
            
    print(len(cards))

    import qrcode
    from PIL import Image, ImageDraw, ImageFont, ImageFilter

    def get_blurred_background(url, width, height):
        response = requests.get(url)
        img = Image.open(BytesIO(response.content))
        img = img.resize((width, height))  # Resize to match the card size
        img = img.filter(ImageFilter.GaussianBlur(radius=5))  # Apply blur effect
        return img

    def create_image(entry):
        filename = f"{entry['song']} [{entry['artists']}] [{entry['year']}].png".replace("/", "_")
        filepath = os.path.join("cards", filename)
        
        if os.path.exists(filepath):
            print(f"Image exists as {filepath}")
            return
        
        # Image dimensions
        img_width, img_height = 800, 400  # Rectangular image, square card
        
        # Create a blank image with a white background
        img = Image.new('RGB', (img_width, img_height), 'black')
        draw = ImageDraw.Draw(img)
        
        # Generate QR code
        qr = qrcode.QRCode(box_size=10, border=2)
        qr.add_data(entry['url'])
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="white", back_color="black")
        qr_size = 200
        qr_img = qr_img.resize((qr_size, qr_size), Image.Resampling.LANCZOS)
        
        # Paste QR code on the left
        img.paste(qr_img, (100, 100))
        
        # Paste bg
        background_img = get_blurred_background(entry["bg_url"], img_width - img_height, img_height)
        right_section_x = img_height
        img.paste(background_img, (right_section_x, 0))
        overlay = Image.new("RGBA", (img_width - img_height, img_height), (0, 0, 0, 210))
        img.paste(overlay, (right_section_x, 0), overlay)
        
        # Fonts
        font_artist = ImageFont.truetype("fonts/Roboto-Light.ttf", 25)
        font_year = ImageFont.truetype("fonts/Roboto-Bold.ttf", 110)
        font_song = ImageFont.truetype("fonts/Roboto-LightItalic.ttf", 25)
        
        # Text positions and content
        artist_text = entry['artists']
        year_text = entry['year']
        song_text = entry['song']
        
        artists_box = (right_section_x, 0, img_width, img_height // 3)
        year_box = (right_section_x, img_height // 3, img_width, 2 * img_height // 3)
        song_box = (right_section_x, 2 * img_height // 3, img_width, img_height)
        
        def draw_centered_text(draw, text, font, color, box, max_width):
            lines = textwrap.wrap(text, width=max_width)
            total_text_height = sum(font.getbbox(line)[3] for line in lines)  # Get height of each line
            y_offset = box[1] + (box[3] - box[1] - total_text_height) // 2
            for line in lines:
                text_width = font.getbbox(line)[2]  # Get width of the line
                x = box[0] + (box[2] - box[0] - text_width) // 2
                draw.text((x, y_offset), line, font=font, fill=color)
                y_offset += font.getbbox(line)[3]  # Increment y-offset by the line height

        draw_centered_text(draw, artist_text, font_artist, "white", artists_box, max_width=26)
        draw_centered_text(draw, year_text, font_year, "white", year_box, max_width=4)
        draw_centered_text(draw, song_text, font_song, "white", song_box, max_width=26)
        
        # Save the image
        try:
            img.save(filepath)
        except OSError as e:
            print(f"Error when saving {filepath}: {e}")
            return
        print(f"Image saved as {filepath}")

    # Generate images for all entries
    import os
    os.makedirs("cards", exist_ok=True)
    cards = sorted(cards, key=lambda x: x["song"])
    for card in cards:
        create_image(card)