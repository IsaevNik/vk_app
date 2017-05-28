import uuid
import logging

from core.utils.cache import uuid_group
from core.vk_integration import vk_integrations
from group.models import Group
from vk_app.celery import app
from core.service import image as image_service

logger = logging.getLogger('celery')


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
