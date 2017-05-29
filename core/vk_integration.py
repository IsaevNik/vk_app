import json
import logging

import requests
from django.conf import settings

logger = logging.getLogger('vk')


class VkApiException(Exception):
    pass


class VKIntegration:

    METHODS = {
        'get_upload_url': 'photos.getOwnerCoverPhotoUploadServer',
        'save_avatar': 'photos.saveOwnerCoverPhoto',
        'user_info': 'users.get'
    }

    def __init__(self):
        self.version = settings.API_VERSION
        self.url = settings.API_URL
        self.not_auth_url = 'https://api.vk.com/method/{api_method}?{params}&v={version}'
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
            response = json.loads(response.content.decode('utf-8'))
            if not response:
                raise VkApiException
            elif 'error' in response:
                logging.error(response)
                raise VkApiException
            return response
        except ValueError:
            raise VkApiException

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
        return response.get('response').get('upload_url')

    def upload_image(self, url, image):
        response = self.request(requests.post, url, files=dict(photo=image))
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
        logging.info('Test info {}'.format(response))
        return True

    def upload_cover(self, image, group):
        try:
            url = self.get_upload_url(group)
            logging.info('Success get url for group (group_id: [{}])'.format(group.group_id))
            hash, photo = self.upload_image(url, image)
            logging.info('Success upload image to server (group_id: [{}])'.format(group.group_id))
            self.set_avatar(hash, photo, group)
            logging.info('Success set url for group (group_id: [{}])'.format(group.group_id))
        except Exception as ex:
            logging.exception('Error in uploading cover to group '
                              '(group_id: [{}])'.format(group.group_id), exc_info=ex)

    def get_profile(self, vk_id):
        params = {
            'user_ids': vk_id,
            'fields': 'photo_200'
        }
        params = '&'.join('{}={}'.format(k, v) for k, v in params.items())
        url = self.not_auth_url.format(api_method=self.METHODS['user_info'], params=params,
                                       version=self.version)
        response = self.request(requests.get, url)
        return response.get('response')

vk_integrations = VKIntegration()
