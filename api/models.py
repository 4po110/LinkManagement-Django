from django.db.models.deletion import CASCADE
from django.conf import settings
from authentication.models import CustomUser
from enum import unique
from django.db import models

# Create your models here.

class Domain(models.Model):
    name = models.CharField(max_length=100, blank=False, null=False, unique=True)

    class Meta:
        db_table = 'Domains'

    def __str__(self):
        return self.name

class File(models.Model):
    type_list = (('JPG','JPG'), ('PNG','PNG'), ('PDF','PDF'), ('DOC','DOC'), ('UNKNOWN','UNKNOWN'))
    name = models.CharField(max_length=255, blank=False, null=False)
    type = models.CharField(max_length=255, choices=type_list, default='UNKNOWN')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    file = models.FileField(upload_to='files/%Y/%m/%d')
    date_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "File"

class Link(models.Model):
    name = models.CharField(max_length=255, blank=False, null=False, unique=True)
    domain = models.ForeignKey(Domain, on_delete=models.CASCADE)
    case = models.CharField(max_length=255, blank=False, null=True)
    folder = models.CharField(max_length=255, blank=False, null=False)
    file = models.ForeignKey(File, blank=True, null=True, on_delete=models.SET_NULL)
    path = models.CharField(max_length=255, blank=False, null=True)

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    created_date = models.DateTimeField(auto_now_add=True)

    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "Link"

    def __str__(self):
        return f'{self.user}_{self.name}'

class LinkAccess(models.Model):
    user = models.ForeignKey(CustomUser, blank=False, null=True, on_delete=models.CASCADE)
    link = models.ForeignKey(Link, blank=False, null=True, on_delete=models.SET_NULL)
    referrer = models.CharField(max_length=512, null=True, blank=True)
    timestamp = models.DateTimeField(null=False, blank=True)
    host = models.CharField(max_length=45, null=False, blank=True)
    agent = models.CharField(max_length=512, null=True, blank=True)
    relevant = models.NullBooleanField(default=None)

    class Meta:
        db_table = "LinkAccessLog"
