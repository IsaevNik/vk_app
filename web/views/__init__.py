from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods

from core.utils.cache import DonateCache, uuid_group
from group.models import Group
from web.forms import EmailForm
from django.conf import settings


@require_http_methods(['GET'])
def index(request):
    return render(request, 'web/index.html')


@require_http_methods(['GET'])
def get_covers(request, uuid):
    group_id = uuid_group.get(uuid)
    uuid_group.delete(uuid)
    if group_id:
        group = Group.objects.filter(group_id=group_id).first()
        if group:
            donates_data = [DonateCache.get_data(id) for id in group.donates_list]
            return render(request, 'web/cover.html', {'donates': donates_data,
                                                      'target': group.active_target})
    return redirect('web:index')


@require_http_methods(['POST'])
def send_email(request):
    form = EmailForm(request.POST)
    if form.is_valid():
        message = 'Имя:{}\nEmail:{}\nСообщение:{}'.format(
            form.cleaned_data.get('name'),
            form.cleaned_data.get('email'),
            form.cleaned_data.get('comment')
        )
        send_mail('new_offer', message,
                  settings.EMAIL_HOST_USER, [settings.EMAIL_HOST_USER])
    return redirect('web:index')
