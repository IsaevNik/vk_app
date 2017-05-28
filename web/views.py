from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods

from core.utils.cache import Donate, uuid_group
from group.models import Group


@require_http_methods(['GET'])
def index(request):
    return render(request, 'web/index.html')


@require_http_methods(['GET'])
def get_covers(request, uuid):
    group_id = uuid_group.get(uuid)
    # uuid_group.delete(uuid)
    if group_id:
        group = Group.objects.filter(group_id=group_id).first()
        if group:
            donates_data = [Donate.get_data(id) for id in group.donates_list]
            return render(request, 'web/cover.html', {'donates': donates_data})
    return redirect('web:index')
