import random

from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods


@require_http_methods(['GET'])
def index(request):
    success = request.session.pop('success', None)
    return render(request, 'web/index.html', {'success': success})


@require_http_methods(['POST'])
def send_comment(request):
    print(request.POST.get('comment'))
    request.session['success'] = random.randint(1, 2)
    return redirect('index')
