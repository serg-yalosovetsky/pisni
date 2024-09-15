import time
import requests
from bs4 import BeautifulSoup
import json



def save_progress(_data, filename='progress.json'):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(_data, f, ensure_ascii=False, indent=4)

def load_progress(filename='progress.json'):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("Файл прогресса не найден. Создаем новый файл.")
        new_data = {'artists_progress': {}, 'songs_progress': {}, 'artists': {}, 'songs': {}}
        save_progress(new_data, filename)
        return new_data

def parse_artists(artists=1000000):
    data = load_progress()
    count_404 = 0
    for i in range(1, artists):
        url = f"https://www.pisni.org.ua/persons/{i}.html"
        print(f"Парсинг артиста {i} из {artists}")

        if url in data['artists_progress']:
            if data['artists_progress'][url]['status'] == 'error':
                count_404 = 0
                continue
            if data['artists_progress'][url]['status'] == 'done':
                continue
        
        retry_delays = [2, 5, 10, 20]
        for delay in retry_delays:
            try:
                response = requests.get(url)
                if response.status_code:
                    break
            except requests.RequestException as e:
                print(f"Ошибка при запросе. Повторная попытка через {delay} секунд.")
                time.sleep(delay)
        else:
            print(f"Не удалось получить данные для артиста {i} после нескольких попыток.")
            data['artists_progress'][url] = {'status': 'error'}
            save_progress(data)
            raise requests.RequestException

        if response.status_code == 404:
            print(f"Артист {i} не найден")
            data['artists_progress'][url] = {'status': 'error'}
            save_progress(data)
            count_404 += 1
            if count_404 >= 1000:
                print("Получено 1000 ошибок 404 подряд. Завершение работы.")
                return
            continue
        count_404 = 0
        
        soup = BeautifulSoup(response.text, 'html.parser')
        is_error = soup.select_one('.error')
        if is_error:
            print(f"Артист {i} не найден")
            data['artists_progress'][url] = {'status': 'error'}
            save_progress(data)
            continue
        
        artist_name = soup.select_one('h1').text.strip()
        href_elements = soup.select('a')
        data['artists'][artist_name] = []
        for a in href_elements:
            href = a.get('href')
            if href and '/songs/' in href:
                href = href.split('#')[0]
                if href not in data['artists'][artist_name]:
                    data['artists'][artist_name].append(href)
        data['artists_progress'][url] = {'status': 'done'}
        save_progress(data)
        print(f"Артист {i} добавлен")


def parse_songs():
    data = load_progress()
    for artist in data['artists']:
        print(f"Парсинг песен артиста {artist}")
        for song in data['artists'][artist]:
            print(f"Парсинг песни {song}")
            _song = song.split('/')[-1]
            _song = _song.split('.')[0]
            url = f"https://www.pisni.org.ua/songs/{_song}.html"
            if url in data['songs_progress'] and data['songs_progress'][url][
                    'status'] == 'done':
                continue
            response = requests.get(url)
            if response.status_code == 404:
                print(f"Песня {song} не найдена")
                data['songs_progress'][url] = {'status': 'error'}
                save_progress(data)
                continue
            soup = BeautifulSoup(response.text, 'html.parser')
            song_name = soup.select_one('.nomarg').text.strip()
            song_text = soup.select_one('.songwords').text.strip()
            data['songs'][song] = {'name': song_name, 'text': song_text}
            data['songs_progress'][url] = {'status': 'done'}
            save_progress(data)
            print(f"Песня {song} добавлена")


if __name__ == '__main__':
    print('Парсинг начат')
    parse_artists()
    print('Парсинг артистов закончен')
    print('Парсинг песен начат')
    parse_songs()
    print('Парсинг песен закончен')
