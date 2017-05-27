from django.conf.urls import url

from web import views

app_name = 'web'

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^covers/(?P<uuid>[0-9\-a-z]+)/$', views.get_covers, name='covers')
    # url(r'^send-comment/$', views.send_comment, name='add_comment')
]