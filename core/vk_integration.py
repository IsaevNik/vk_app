import json

import requests
from django.conf import settings


class VKIntegration:

    METHODS = {
        'get_upload_url': 'photos.getOwnerCoverPhotoUploadServer',
        'save_avatar': 'photos.saveOwnerCoverPhoto'
    }

    def __init__(self):
        self.token = settings.API_ACCESS_TOKEN
        self.version = settings.API_VERSION
        self.url = settings.API_URL
        self.group_id = settings.GROUP_ID
        # https://api.vk.com/method/{api_method}?{params}&access_token={token}&v={version}

    def request(self, http_method, url, **kwargs):
        """
        Request & Response with SteamTread
        :return:        Десериализованный ответ
        """
        data = kwargs.get('data')
        files = kwargs.get('files')
        response = http_method(url=url, data=data, files=files)
        try:
            return json.loads(response.content.decode('utf-8'))
        except ValueError:
            return None

    def get_upload_url(self):
        params = {
            'corp_x': 0,
            'corp_y': 0,
            'crop_x2': 1590,
            'crop_y2': 400,
            'group_id': self.group_id
        }
        params = '&'.join('{}={}'.format(k, v) for k, v in params.items())
        url = self.url.format(api_method=self.METHODS['get_upload_url'], params=params,
                              token=self.token, version=self.version)
        response = self.request(requests.get,  url)
        if response:
            return response.get('response').get('upload_url')

    def upload_image(self, url, image):
        response = self.request(requests.post, url, files=dict(photo=image))
        if response:
            return response.get('hash'), response.get('photo')

    def set_avatar(self, hash, photo):
        params = {
            'photo': photo,
            'hash': hash,
        }
        params = '&'.join('{}={}'.format(k, v) for k, v in params.items())
        url = self.url.format(api_method=self.METHODS['save_avatar'], params=params,
                              token=self.token, version=self.version)
        response = self.request(requests.get, url)
        if response:
            print(response)
            return True

    def upload_cover(self, image):
        url = self.get_upload_url()
        hash, photo = self.upload_image(url, image)
        self.set_avatar(hash, photo)


vk_integrations = VKIntegration()
