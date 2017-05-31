import uuid
import logging

from core.utils.cache import uuid_group
from core.utils.payment import cash_sender
from core.vk_integration import vk_integrations
from group.models import CashSend
from group.models import Group
from vk_app.celery import app
from core.service import image as image_service

logger = logging.getLogger('celery')


class ProcessNoFinished(Exception):
    pass


@app.task(name='set_cover')
def set_cover(group_id):
    logger.info('Set cover start for group: [{}]'.format(group_id))
    group = Group.objects.filter(group_id=group_id).first()
    if group:
        key = uuid.uuid4()
        uuid_group.set(key, group.group_id)
        logger.info('Set group: [{}] to cache with uuid: [{}]'.format(group_id, key))
        try:
            path_to_cover = image_service.create_image(group, str(key))
        except Exception as ex:
            logging.exception('Error in cloudconvert', exc_info=ex)
            return
        logger.info('Success create and save image for '
                    'group: [{}] to path [{}]'.format(group_id, path_to_cover))
        with open(path_to_cover, 'rb') as payload:
            vk_integrations.upload_cover(payload, group)
        logging.info('Success set cover for group: [{}]'.format(group_id))


@app.task(bind=True, name='check_cash_send', max_retries=6)
def check_cash_send(self, cash_send_id):
    cash_send = CashSend.objects.filter(id=cash_send_id).first()
    if cash_send:
        try:
            logger.info('Try to send payment_id [{}] (retry №[{}])'.format(
                cash_send.payment_id, self.request.retries))
            status = cash_sender.get_status(cash_send.payment_id)
            if not status:
                logger.info('No status for payment_id [{}] (retry №[{}])'.format(
                    cash_send.payment_id, self.request.retries))
                raise ProcessNoFinished

            logger.info('Payment_id [{}] has status [{}] (retry №[{}])'.format(
                cash_send.payment_id, status, self.request.retries))
            cash_send.status = CashSend.STATUSES_MAP.get(status)
            cash_send.save()

            if status not in ['Completed', 'Canceled']:
                raise ProcessNoFinished

        except ProcessNoFinished as exc:
            self.retry(exc=exc, countdown=4 * 60 * 60)
