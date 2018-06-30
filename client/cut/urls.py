from django.conf.urls import url

from cut import views


urlpatterns = [
    url('^start$', views.start, name="start"),
]
