import hmac
import json
import random
from _sha256 import sha256
from copy import copy

from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw

from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods

from core.vk_integration import vk_integrations


@require_http_methods(['GET'])
def index(request):
    user_data = None
    success = request.session.pop('success', None)
    request_data = copy(request.GET)
    # check_sign(request_data)
    api_data = request_data.get('api_result')
    if api_data:
        response = json.loads(api_data).get('response')
        if response:
            user_data = response[0]
            request.session['user_data'] = user_data
    else:
        user_data = request.session.get('user_data')
    return render(request, 'web/index.html',
                  {'success': success, 'user': user_data})


@require_http_methods(['POST'])
def send_comment(request):
    text = request.POST.get('comment', '')
    img = Image.new('RGB', (1590, 400), color=(random.randint(0, 255),
                                               random.randint(0, 255),
                                               random.randint(0, 255))
                    )
    draw = ImageDraw.Draw(img)

    font = ImageFont.truetype("KhmerOS.ttf", 24)
    # draw.text((x, y),"Sample Text",(r,g,b))
    draw.text((60, 80), text, (0, 0, 0), font=font)
    img.save('sample-out.jpg')
    with open('sample-out.jpg', 'rb') as payload:
        url = vk_integrations.upload_avatar(payload)
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
