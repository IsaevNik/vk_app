import os
import random
import uuid
import requests

from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw

from django.conf import settings

from core.utils.cache import donates, donates_list


def create_image():
    background = Image.new('RGB', (1590, 400), color=(random.randint(0, 255),
                                               random.randint(0, 255),
                                               random.randint(0, 255))
                 )
    text_draw = ImageDraw.Draw(background)
    font = ImageFont.truetype(settings.FONT, 28)
    username_font = ImageFont.truetype(settings.FONT, 34)
    donates_data = [donates.get_all(id) for id in donates_list]
    avatars = []
    for donate in donates_data:
        im = Image.open(donate.get('avatar'))
        size = (im.size[0] * 3, im.size[1] * 3)
        mask = Image.new('L', size, 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0) + size, fill=255)
        mask = mask.resize(im.size, Image.ANTIALIAS)
        im.putalpha(mask)
        im.thumbnail((90, 90), Image.ANTIALIAS)
        avatars.append(im)
    texts = [donate.get('text') for donate in donates_data]
    names = ['{} {}'.format(donate.get('first_name'), donate.get('last_name'))
             for donate in donates_data]

    render_data = zip(avatars, texts, names)
    x_start = 20
    y_start = 20
    for i, item in enumerate(render_data):
        background.paste(item[0], (x_start, y_start + i * (45 + 90)), item[0])
        text_draw.text((x_start + 140, y_start + i * (45 + 90)), item[2], (255, 255, 255), font=username_font)
        text_draw.text((x_start + 120, y_start + 45 + i * (45 + 90)), item[1], (0, 0, 0), font=font)

    file_name = os.path.join(settings.MEDIA_ROOT, 'covers', str(uuid.uuid4())) + '.jpg'
    background.save(file_name)
    return file_name


def save_avatar(url):
    file_name = os.path.join(settings.MEDIA_ROOT, 'avatars', str(uuid.uuid4())) + '.jpg'
    page = requests.get(url)
    with open(file_name, 'wb') as fd:
        fd.write(page.content)
    return file_name
