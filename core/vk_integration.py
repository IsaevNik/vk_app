import json

import requests
from django.conf import settings


class VKIntegration:

    METHODS = {
        'get_upload_url': 'photos.getOwnerCoverPhotoUploadServer',
        'save_avatar': 'photos.saveOwnerCoverPhoto'
    }

    def __init__(self):
        self.version = settings.API_VERSION
        self.url = settings.API_URL
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

    def get_upload_url(self, group):
        params = {
            'corp_x': 0,
            'corp_y': 0,
            'crop_x2': 1590,
            'crop_y2': 400,
            'group_id': group.group_id
        }
        params = '&'.join('{}={}'.format(k, v) for k, v in params.items())
        url = self.url.format(api_method=self.METHODS['get_upload_url'], params=params,
                              token=group.access_token, version=self.version)
        response = self.request(requests.get,  url)
        if response:
            return response.get('response').get('upload_url')

    def upload_image(self, url, image):
        response = self.request(requests.post, url, files=dict(photo=image))
        if response:
            return response.get('hash'), response.get('photo')

    def set_avatar(self, hash, photo, group):
        params = {
            'photo': photo,
            'hash': hash,
        }
        params = '&'.join('{}={}'.format(k, v) for k, v in params.items())
        url = self.url.format(api_method=self.METHODS['save_avatar'], params=params,
                              token=group.access_token, version=self.version)
        response = self.request(requests.get, url)
        if response:
            print(response)
            return True

    def upload_cover(self, image, group):
        url = self.get_upload_url(group)
        hash, photo = self.upload_image(url, image)
        self.set_avatar(hash, photo, group)


vk_integrations = VKIntegration()
