import yt_dlp

# Function to download songs from YouTube playlist
def download_songs_from_playlist(playlist_url, output_path='./downloads'):
    # Options for yt-dlp
    ydl_opts = {
        'format': 'bestaudio/best',   # Download best quality audio available
        'outtmpl': f'{output_path}/%(title)s.%(ext)s',  # Output path and filename
        'postprocessors': [{   # Use ffmpeg to convert to mp3
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '320',
        }],
        'noplaylist': False,  # Ensure the entire playlist is downloaded
    }

    # Initialize yt-dlp with options
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([playlist_url])

# Replace with your YouTube playlist URL
playlist_url = 'https://www.youtube.com/playlist?list=PLEJYPrcLjkrViJpaliSuODRtJC0ILQzSA'
download_songs_from_playlist(playlist_url)