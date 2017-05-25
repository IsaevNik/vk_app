from django.conf.urls import url

from vk import views

app_name = 'vk'

urlpatterns = [
    url(r'^$', views.app_index, name='index'),
    url(r'^send-comment/$', views.app_send_comment, name='add_comment')
]