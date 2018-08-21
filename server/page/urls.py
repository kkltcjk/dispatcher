from django.conf.urls import url

from page import views


urlpatterns = [
    url('^tasks$', views.tasks, name="tasks"),
    url('^detail$', views.detail, name="detail"),
]
