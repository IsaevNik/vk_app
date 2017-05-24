import os
import random
import uuid
import requests

from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw

from django.conf import settings

from core.utils.cache import Donate


def create_image(group):
    background = Image.new('RGB', (1590, 400),
                           color=(random.randint(0, 255),
                                  random.randint(0, 255),
                                  random.randint(0, 255))
                           )
    text_draw = ImageDraw.Draw(background)
    font = ImageFont.truetype(settings.FONT, 28)
    username_font = ImageFont.truetype(settings.FONT, 34)
    donates_data = [Donate.get_data(id) for id in group.donates_list]
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

    file_name = os.path.join(group.covers_path, str(uuid.uuid4())) + '.png'
    background.save(file_name, 'PNG')
    return file_name


def save_avatar(url, group):
    if not url:
        file_name = settings.DEFAULT_AVATAR
        return file_name
    if not os.path.exists(group.avatars_path):
        os.makedirs(group.avatars_path)
    file_name = os.path.join(group.avatars_path, str(uuid.uuid4())) + '.png'
    page = requests.get(url)
    with open(file_name, 'wb') as fd:
        fd.write(page.content)
    return file_name
