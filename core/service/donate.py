import time
from django.db import transaction

from core.utils.cache import DonateCache
from group.models import Donate
from group.models import Order
from core.vk_integration import vk_integrations
from core.service import image as image_service
from core.utils.tasks import set_cover


class TargetDoesNotExist(Exception):
    pass


def create_donate(vk_id, group, amount, comment):
    target = group.targets.filter(active=True).first()
    if not target:
        raise TargetDoesNotExist
    with transaction.atomic():
        donate = Donate.objects.create(vk_id=vk_id, comment=comment, target=target)
        order = Order.objects.create(donate=donate, amount=amount)

    return order


def accept_donate(data):
    order_id = data.get('MERCHANT_ORDER_ID')
    cur_id = data.get('CUR_ID')
    intid = data.get('intid')
    order = Order.objects.select_related('donate', 'donate__target__group').get(id=order_id)
    order.cur_id = int(cur_id)
    order.transaction_id = int(intid)
    order.status = Order.DEPOSITED
    order.save()
    return order


def send_donate(order):
    num = int(time.time() * 1000)
    profile = vk_integrations.get_profile(order.donate.vk_id)
    if profile:
        user_data = profile[0]
        group = order.donate.target.group
        path_to_avatar = image_service.save_avatar(user_data.get('photo_200'), group)
        DonateCache.create(group, num, order.donate.comment, path_to_avatar, order.amount, user_data)
        set_cover.delay(group.group_id)

