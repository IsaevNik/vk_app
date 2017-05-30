import logging

from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from core.utils.payment import payment_facade
from core.service import donate as donate_service
from group.models import Order

logger = logging.getLogger('payment')


@require_http_methods(['GET'])
def process(request):
    logger.info(request.GET)
    order_id = payment_facade.check_sign(request.GET)
    if order_id:
        try:
            order = donate_service.accept_donate(request.GET)
            donate_service.send_donate(order)
        except Order.DoesNotExist:
            logger.error('Order does not exist')
    else:
        logger.error('Sign checking fail')


@require_http_methods(['GET'])
def success(request):
    user_data = request.session.get('user_data')
    data = dict(user=user_data, status='success')
    return render(request, 'app/before.html', data)


@require_http_methods(['GET'])
def fail(request):
    user_data = request.session.get('user_data')
    data = dict(user=user_data, status='fail', error='Произошла ошибка при оплате')
    return render(request, 'app/before.html', data)
