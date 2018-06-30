from django.conf.urls import url

from task import views


urlpatterns = [
    url('^start$', views.start, name="start"),
    url('^update$', views.update, name="update"),
    url('^tasks$', views.tasks, name="tasks"),
]
