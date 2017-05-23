import hmac
import json
import random
from _sha256 import sha256
from copy import copy

import time
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods

from core.service import user as user_service
from core.service import image as image_service
from core.utils.cache import donates
from core.vk_integration import vk_integrations


@require_http_methods(['GET'])
def index(request):
    success = request.session.pop('success', None)
    request_data = copy(request.GET)
    # check_sign(request_data)
    api_data = request_data.get('api_result')
    if api_data:
        user_data = user_service.get_user_info(api_data)
        request.session['user_data'] = user_data
    else:
        user_data = request.session.get('user_data')
    return render(request, 'web/index.html',
                  {'success': success, 'user': user_data})


@require_http_methods(['POST'])
def send_comment(request):
    text = request.POST.get('comment', '')
    user_data = request.session.get('user_data')
    if user_data:

        num = int(time.time() * 1000)
        path_to_avatar = image_service.save_avatar(user_data.get('photo_200'))
        donates.create(num, text, path_to_avatar, user_data)

        path_to_image = image_service.create_image()

        with open(path_to_image, 'rb') as payload:
            vk_integrations.upload_cover(payload)
        request.session['success'] = random.randint(1, 2)
    return redirect('index')


def check_sign(params):
    sign = params.pop('sign', [None])[0]
    secret = b'fwVSwoVVmdRRbURSP5UJ'
    # Удаление пустых параметров
    params = dict((key, val) for key, val in params.items() if key not in ['hash', 'sign', 'api_result'])
    # Конкатенация параметров с алфавитной сортировкой
    sorted_string = ''.join('{}'.format(val) for val in params.values())
    c = hmac.new(secret, sorted_string.encode('utf-8'), sha256).hexdigest()
    print(c)
    print(sign)
    return True
