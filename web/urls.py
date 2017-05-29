from django.conf.urls import url

from web.views import index, get_covers
from web.views import payment

app_name = 'web'

urlpatterns = [
    url(r'^$', index, name='index'),
    url(r'^covers/(?P<uuid>[0-9\-a-z]+)/$', get_covers, name='covers'),
    url(r'^payment/$', payment.process),
    url(r'^payment/success/$', payment.success),
    url(r'^payment/fail/$', payment.fail),
]