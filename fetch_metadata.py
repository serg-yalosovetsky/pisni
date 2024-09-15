import json
import os
import requests
import yt_dlp
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TALB, COMM
from mutagen.id3 import APIC

default_filename = 'progress_youtube.json'

def save_progress(_data, filename=default_filename):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(_data, f, ensure_ascii=False, indent=4)

def load_progress(filename=default_filename):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("Файл прогресса не найден. Создаем новый файл.")
        new_data = {'artists_progress': {}, 'songs_progress': {}, 'artists': {}, 'songs': {}}
        save_progress(new_data, filename)
        return new_data
    

def get_playlist_videos(playlist_url):
    ydl_opts = {
        'extract_flat': True,  # Extract only metadata, no downloading
        'skip_download': True,  # Do not download any video
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        result = ydl.extract_info(playlist_url, download=False)

    if 'entries' in result:
        videos = [{'id': video['id'], 
                   'title': video['title'], 
                   'channel': video['channel'], 
                   'description': video['description'], 
                   'duration': video['duration'], 
                   'thumbnail': video['thumbnails'][-1]['url'], 
                   'uploader': video['uploader']} 
                   for video in result['entries']]
        return videos
    else:
        return []

    
def statistics(data):
    done = len([video for video in data['songs_progress'].values() if video['status'] == 'done'])
    error = len([video for video in data['songs_progress'].values() if video['status'] == 'error'])
    print(f"Всего: {done + error}")
    print(f"Успешно: {done}")
    print(f"Ошибки: {error}")
    data['statistics'] = {'done': done, 'error': error}
    save_progress(data)


def download_songs(videos, output_path='./downloads', stop=-1):
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
        'cookiesfrombrowser': ('firefox',),  # Использовать куки из Chrome
        'nocheckcertificate': True,
        'ignoreerrors': True,
        'no_warnings': True,
    }
    data = load_progress()
    # Initialize yt-dlp with options
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        for i, video in enumerate(videos):
            print(f"start {i+1} из {len(videos)}")

            if video.get('id') in data['songs_progress']:
                if data['songs_progress'][video.get('id')] and data['songs_progress'][video.get('id')].get('status') == 'done':
                    print(f"skip {i+1} из {len(videos)}, {video.get('id')} is done")
                    continue

            stop -= 1
            if stop == 0:
                break
            filename_without_ext = None
            info = None
            try:
                url = f"https://www.youtube.com/watch?v={video['id']}"

                info = ydl.extract_info(url, download=False)
                if info is None:
                    raise Exception(f"Error extracting info for video {video['id']}: Video unavailable")
                filename = ydl.prepare_filename(info)
                filename_without_ext = os.path.splitext(filename)[0]
                
                if not os.path.exists(f"{filename_without_ext}.mp3"):
                    ydl_opts['postprocessors'].append({
                        'key': 'FFmpegMetadata',
                        'add_metadata': True,

                    })
                    ydl.download([url])
                else:
                    print(f"skip {i+1} из {len(videos)}, {video.get('id')} is downloaded")
                    print(f"Файл {filename_without_ext}.mp3 уже существует")
                    data['songs_progress'][video['id']] = {'status': 'done'}
                    save_progress(data)
                    continue
                
                # Сохраняем метаданные в файл MP3
                metadata = {
                    'title': info.get('title'),
                    'artist': info.get('uploader'),
                    'album': info.get('channel'),
                    'description': info.get('description'),
                }
                
                audio = MP3(f"{filename_without_ext}.mp3", ID3=ID3)
                if audio.tags is None:
                    audio.add_tags()
                
                audio.tags.add(TIT2(encoding=3, text=metadata['title']))
                audio.tags.add(TPE1(encoding=3, text=metadata['artist']))
                audio.tags.add(TALB(encoding=3, text=metadata['album']))
                audio.tags.add(COMM(encoding=3, lang='rus', desc='Description', text=metadata['description']))
                
                # Добавляем обложку
                if 'thumbnail' in info:
                    thumbnail_url = info['thumbnail']
                    thumbnail_data = requests.get(thumbnail_url).content
                    audio.tags.add(APIC(
                        encoding=3,
                        mime='image/jpeg',
                        type=3,  # 3 означает обложку
                        desc='Cover',
                        data=thumbnail_data
                    ))
                
                audio.save()
                data['songs_progress'][video['id']] = {'status': 'done'}
                data['songs'][video['id']] = {'metadata': info, 'filename': filename_without_ext, 'url': url}
                save_progress(data)
                # Удаляем файл m4a, если доступен mp3
                m4a_file = f"{filename_without_ext}.m4a"
                mp3_file = f"{filename_without_ext}.mp3"
                if os.path.exists(mp3_file):
                    if os.path.exists(m4a_file):
                        os.remove(m4a_file)
                        print(f"Файл {m4a_file} удален")
                # Сохраняем метаданные в JSON файл
                # with open(f"{filename_without_ext}_metadata.json", 'w', encoding='utf-8') as f:
                #     json.dump(metadata, f, ensure_ascii=False, indent=4)
                print(f"Обработано {i+1} из {len(videos)}")
            except Exception as e:
                print(f"Error downloading video {video['id']} # {i+1} из {len(videos)}: {e}")
                data['songs_progress'][video['id']] = {'status': 'error', 'error': str(e)}
                data['songs'][video['id']] = {'metadata': info, 'filename': filename_without_ext, 'url': url}
                save_progress(data)
                print(f"Error downloading video {video['id']}: {e}")
    statistics(data)



# Example usage
playlist_url = 'https://www.youtube.com/playlist?list=PLEJYPrcLjkrViJpaliSuODRtJC0ILQzSA'
videos = get_playlist_videos(playlist_url)

download_songs(videos)