import time
import requests
from bs4 import BeautifulSoup
import json
import re
from lxml import html


FILENAME = 'progress_azlyrics.json'
LETTERS = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', '19']

def save_progress(_data, filename=FILENAME):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(_data, f, ensure_ascii=False, indent=4)

def load_progress(filename=FILENAME):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("Файл прогресса не найден. Создаем новый файл.")
        new_data = {'letters_progress': {}, 'artists_progress': {}, 'songs_progress': {}, 'artists': {}, 'songs': {}, 'letters': {}}
        save_progress(new_data, filename)
        return new_data


def parse_letters():
    pattern = r'^([a-z]|19)/([a-z0-9]+)\.html$'
    data = load_progress()
    for letter in LETTERS:
        url = f"https://www.azlyrics.com/{letter}.html"
        print(f"parsing artists from letter {letter}")

        if url in data['letters_progress']:
            if data['letters_progress'][url]['status'] == 'error' or data['letters_progress'][url]['status'] == 'done':
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
            print(f"Не удалось получить данные для letter {letter} после нескольких попыток.")
            data['letters_progress'][url] = {'status': 'error'}
            save_progress(data)
            raise requests.RequestException

        if response.status_code == 404:
            print(f"letter {letter} not found")
            data['letters_progress'][url] = {'status': 'error'}
            save_progress(data)
            continue

        soup = BeautifulSoup(response.text, 'html.parser')
        is_error = soup.select_one('.error')
        if is_error:
            print(f"letter {letter} not found")
            data['letters_progress'][url] = {'status': 'error'}
            save_progress(data)
            continue
        
        href_elements = soup.select('a')
        for a in href_elements:
            href = a.get('href')
            if href:
                match = re.match(pattern, href)
                if match:
                    if match[1] not in data['letters']:
                        data['letters'][match[1]] = []
                    if match[2] not in data['letters'][match[1]]:
                        data['letters'][match[1]].append(match[2])
        data['letters_progress'][url] = {'status': 'done'}
        save_progress(data)
        print(f"letter {letter} added")
        
        
def parse_artists():
    data = load_progress()
    pattern = r'^/lyrics/([a-z0-9]+)/([a-z]+)\.html$'
    for letter in data['letters']:
        for artist in data['letters'][letter]:
            url = f"https://www.azlyrics.com/{letter}/{artist}.html"
            print(f"Парсинг артиста {artist} из {letter}")

            if url in data['artists_progress']:
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
                
                print(f"Не удалось получить данные для артиста {artist} после нескольких попыток.")
                data['artists_progress'][url] = {'status': 'error'}
                save_progress(data)
                raise requests.RequestException

            if response.status_code == 404:
                print(f"Артист {artist} не найден")
                data['artists_progress'][url] = {'status': 'error'}
                save_progress(data)
                continue
            
            soup = BeautifulSoup(response.text, 'html.parser')
            is_error = soup.select_one('.error')
            if is_error:
                print(f"Артист {artist} не найден")
                data['artists_progress'][url] = {'status': 'error'}
                save_progress(data)
                continue
            
            artist_name = soup.select_one('h1').text.strip().replace(' Lyrics', '').replace('Lyrics', '')
            href_elements = soup.select('a')
            data['artists'][artist_name] = []
            for a in href_elements:
                href = a.get('href')
                if href:    
                    match = re.match(pattern, href)
                    if match:
                        if match.group(2) not in data['artists'][artist_name]:
                            data['artists'][artist_name].append(match.group(2))
            data['artists_progress'][url] = {'status': 'done'}
            save_progress(data)
            print(f"Артист {artist} добавлен")

def parse_songs():
    data = load_progress()
    for artist in data['artists']:
        print(f"Парсинг песен артиста {artist}")
        for song in data['artists'][artist]:
            print(f"Парсинг песни {song}")
            url = f"https://www.azlyrics.com/lyrics/{artist}/{song}.html"
            if url in data['songs_progress'] and data['songs_progress'][url]['status'] == 'done':
                continue
            response = requests.get(url)
            if response.status_code == 404:
                print(f"Песня {song} не найдена")
                data['songs_progress'][url] = {'status': 'error'}
                save_progress(data)
                continue
            soup = BeautifulSoup(response.text, 'html.parser')
            tree = html.fromstring(response.content)
            song_name = soup.select_one('h1').text.strip().replace(' lyrics', '').replace('lyrics', '').replace('"', '')
            song_text = tree.xpath('//div[@class="row"]/div[2]/div')[4].text_content()
            data['songs'][song_name] = {'name': song_name, 'text': song_text}
            data['songs_progress'][url] = {'status': 'done'}
            save_progress(data)
            print(f"Песня {song} добавлена")

if __name__ == '__main__':
    print('Парсинг начат')
    parse_letters()
    print('Парсинг букв закончен')
    print('Парсинг артистов начат')
    parse_artists()
    print('Парсинг артистов закончен')
    print('Парсинг песен начат')
    parse_songs()
    print('Парсинг песен закончен')
