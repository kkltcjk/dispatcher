from django.db import models

# Create your models here.
class Task(models.Model):
    name = models.CharField(max_length=100, unique=True)
    procedure = models.CharField(max_length=30)
    detail = models.TextField()
