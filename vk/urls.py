from django.conf.urls import url

from vk import views


urlpatterns = [
    url(r'^$', views.app_index, name='index'),
    url(r'^donate/$', views.donate, name='make_donate')
]
