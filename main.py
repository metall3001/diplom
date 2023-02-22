import string
from pprint import pprint
import json
import requests as requests


def file_from_vk(owner_id: string, token_vk: string):
    url = 'https://api.vk.com/method'
    url_photo = url + '/photos.get'
    url_user = url + '/users.get'
    params = {
        'user_ids': owner_id,
        'access_token': token_vk,
        'v': '5.131',
    }
    if not owner_id.isdecimal():
        response = requests.get(url_user, params=params).json()
        if 'error' in response:
            print('Ошибка с определением ID - ', response['error']['error_msg'])
            return
        owner_id = response['response'][0]['id']
    params = {
        'owner_id': owner_id,
        'access_token': token_vk,
        'album_id': 'profile',
        'v': '5.131',
        'extended': '1',
        'photo_sizes': '1'
    }
    photos_vk = []
    response = requests.get(url_photo, params=params).json()
    if 'response' in response:
        photo_count = (response['response']['count'])
        print('Запрос на скачивание фото из контакта успешен')
        if photo_count == 0:
            print('В этом аккаунте нет фото в профиле')
            return
        print(f'В этом аккаунте {photo_count} фото в профиле')
        photo_count = int(input('Сколько фото нужно скачать:\n'))
        i = 0
        for items in response['response']['items']:
            i += 1
            if i > photo_count:
                break
            print(f'Скачиваем фото {items["id"]}')
            photos_vk.append(max_photo_size(items))
        return photos_vk
    else:
        print('Ошибка - ', response['error']['error_msg'])
        return


def max_photo_size(item):
    vk_photo_sizes = {
        's': 75,
        'm': 130,
        'x': 604,
        'y': 807,
        'z': 1080,
        'w': 2560,
        'o': 130,
        'p': 200,
        'r': 510
    }
    max_size = 0
    photo = ''
    photo_size = ''
    for sizes in item['sizes']:
        size = sizes['width'] * sizes['height']
        if size == 0:
            size = vk_photo_sizes[sizes['type']]
        if size >= max_size:
            max_size = size
            photo = sizes['url']
            photo_size = sizes['type']
    return {'date': item['date'],
            'likes': item['likes']['count'],
            'photo_url': photo,
            'size': photo_size}


def file_to_disk(photos_disk: list, OAuth: string):
    resource_url = "https://cloud-api.yandex.net/v1/disk/resources"
    headers = {'Content-Type': 'application/json',
               'Authorization': 'OAuth {}'.format(OAuth)}
    response = requests.put(resource_url, headers=headers, params={'path': 'vk/'})
    if response.status_code == 201 or response.status_code == 409:
        print('ЯДиск готов принимать файлы')
        info_json = []
        name_list = []
        for photo in photos_disk:
            name = post_file(photo, name_list, headers)
            name_list.append(name)
            info_json.append({'file_name': name,
                              'size': photo['size']})
    else:
        print('Ошибка при подключении к ЯДиску -', response.json()['message'])
        return
    return info_json


def post_file(photo, name_list, headers):
    upload_url = 'https://cloud-api.yandex.net/v1/disk/resources/upload'
    name = str(photo['likes'])
    if name in name_list:
        name += str(photo['date'])
    params = {'url': photo['photo_url'],
              'path': 'vk/' + name}
    response = requests.post(upload_url, headers=headers, params=params)
    if response.status_code == 202:
        print(f'Файл {name} загружен на ЯДиск')
        return name
    else:
        print('Ошибка при загрузке фото -', response.json()['message'])
        return


if __name__ == "__main__":
    id_vk = input('Введите username или id пользователя vk:\n')
    token = input('Введите ключ доступа vk:\n')
    photos = file_from_vk(id_vk, token)
    if photos:
        token = input('Введите токен с Полигона Яндекс.Диска:\n')
        json_ = file_to_disk(photos, token)
        if json_:
            with open("photo_from_vk.json", 'w') as json_file:
                json.dump(json_, json_file)
            print('Выходной файл:')
            pprint(json_)
    else:
        print('Ой все, беда!')