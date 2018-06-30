from django.conf.urls import url

from cluster import views


urlpatterns = [
    url('^start$', views.start, name="start"),
]
