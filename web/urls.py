from django.conf.urls import url

from web.views import index, get_covers, payment, send_email

app_name = 'web'

urlpatterns = [
    url(r'^$', index, name='index'),
    url(r'^covers/(?P<uuid>[0-9\-a-z]+)/$', get_covers, name='covers'),
    url(r'^send-email/$', send_email, name='send-email'),
    url(r'^payment/$', payment.process),
    url(r'^payment/success/$', payment.success),
    url(r'^payment/fail/$', payment.fail),
]