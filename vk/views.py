import hmac
import random
from _sha256 import sha256
from copy import copy

import time
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from core.utils.tasks import set_cover

from core.service import user as user_service
from core.service import image as image_service
from core.utils.cache import Donate
from group.models import Group


@require_http_methods(['GET'])
def app_index(request):
    success = request.session.pop('success', None)
    request_data = copy(request.GET)
    # check_sign(request_data)
    api_data = request_data.get('api_result')
    group_id = request_data.get('group_id')
    if api_data and group_id:
        user_data = user_service.get_user_info(api_data)
        request.session['user_data'] = user_data
        request.session['group_id'] = group_id
    else:
        user_data = request.session.get('user_data')
    return render(request, 'app/index.html',
                  {'success': success, 'user': user_data})


@require_http_methods(['POST'])
def app_send_comment(request):
    group = None
    text = request.POST.get('comment', '')
    user_data = request.session.get('user_data')
    group_id = request.session.pop('group_id', None)
    if group_id:
        group = Group.objects.filter(group_id=group_id).first()
    if user_data and group:
        num = int(time.time() * 1000)
        path_to_avatar = image_service.save_avatar(user_data.get('photo_200'), group)
        Donate.create(group, num, text, path_to_avatar, user_data)

        set_cover.delay(group_id)
    request.session['success'] = random.randint(1, 2)
    return redirect('vk:index')


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

