import hmac
import random
from _sha256 import sha256
from copy import copy

import time

import requests
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods

from core.utils.payment import payment_facade
from core.utils.tasks import set_cover

from core.service import user as user_service
from core.service import image as image_service
from core.service import donate as donate_service
from core.utils.cache import DonateCache
from group.models import Group
from vk.forms import DonateForm


@require_http_methods(['GET'])
def app_index(request):
    request_data = copy(request.GET)
    api_data = request_data.get('api_result')
    vk_id = request_data.get('viewer_id')
    group_id = request_data.get('group_id')
    if api_data and group_id:
        user_data = user_service.get_user_info(api_data)
        request.session['user_data'] = user_data
        request.session['group_id'] = group_id
        request.session['vk_id'] = vk_id
    else:
        user_data = request.session.get('user_data')
    return render(request, 'app/index.html',
                  {'user': user_data})


@require_http_methods(['POST'])
def donate(request):
    render_data = {}
    form = DonateForm(request.POST)
    user_data = request.session.get('user_data')
    vk_id = request.session.get('vk_id', None)
    group_id = request.session.get('group_id', None)
    if form.is_valid():
        if group_id and vk_id:
            group = Group.objects.filter(group_id=group_id).first()
            if group:
                amount = form.cleaned_data.get('amount')
                if amount < group.min_donate:
                    render_data['error'] = 'Администрация сообщества ' \
                                           'установила величину минимального ' \
                                           'доната в {} рублей'.format(group.min_donate)
                else:
                    comment = form.cleaned_data.get('comment', '')
                    order = donate_service.create_donate(vk_id, group, amount, comment)
                    terminal_url = payment_facade.get_terminal(amount, order.id)
                    return redirect(terminal_url)
            else:
                render_data['error'] = 'Такая группа не зарегестрирована у нас в системе'
        else:
            render_data['error'] = 'Нужно зайти из vk.com'
    else:
        render_data['error'] = 'Проверьте правильность введённых данных'
    render_data['user'] = user_data
    render_data['group_id'] = group_id
    render_data['status'] = 'fail'
    # text = request.POST.get('comment', '')
    # user_data = request.session.get('user_data')
    # group_id = request.session.pop('group_id', None)
    # if group_id:
    #     group = Group.objects.filter(group_id=group_id).first()
    # if user_data and group:
    #     num = int(time.time() * 1000)
    #     path_to_avatar = image_service.save_avatar(user_data.get('photo_200'), group)
    #     Donate.create(group, num, text, path_to_avatar, user_data)
    #
    #     set_cover.delay(group_id)

    return render(request, 'app/before.html', render_data)


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

