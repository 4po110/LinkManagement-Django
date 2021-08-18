import os
from api.models import Link, File, Domain, LinkAccess
from authentication.models import CustomUser
from rest_framework import serializers

from authentication.models import CustomUser, LoginLog

class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = CustomUser
        fields = ('id', 'username', 'email', 'date_joined', 'last_login')

class LoginSerializer(serializers.ModelSerializer):

    # customuser = UserSerializer

    class Meta:
        model = LoginLog
        fields = ('user', 'session_key', 'host', 'login_time')

class LoginAllSerializer(serializers.ModelSerializer):

    # customuser = UserSerializer

    class Meta:
        model = LoginLog
        fields = ('user_id', 'host', 'login_time')

class DomainSerializer(serializers.ModelSerializer):

    class Meta:
        model = Domain
        fields = '__all__'

class FileSerializer(serializers.ModelSerializer):

    class Meta:
        model = File
        fields = ('name', 'type', 'user', 'file', 'date_created')

class FileListSerializer(serializers.ModelSerializer):

    file = serializers.CharField(source='file.name')
    user = serializers.CharField(source="user.username")

    class Meta:
        model = File
        fields = ('id', 'name', 'type', 'user', 'file', 'date_created')

class LinkSerializer(serializers.ModelSerializer):

    class Meta:
        model = Link
        fields = ('name', 'domain', 'case', 'folder', 'file', 'path', 'user', 'created_date')

class LinkListSerializer(serializers.ModelSerializer):

    domain = serializers.CharField(source='domain.name')
    file = serializers.CharField(source='file.name', required=False, allow_blank=True)
    # user = serializers.CharField(source="user.username")

    class Meta:
        model = Link
        fields = ('id', 'name', 'domain', 'case', 'folder', 'file', 'path', 'created_date')

class AccessSerializer(serializers.ModelSerializer):

    domain = serializers.CharField(source='link.domain')
    link_id = serializers.CharField(source='link.id')
    url = serializers.CharField(source='link.path')
    case = serializers.CharField(source='link.case')
    name = serializers.CharField(source='link.name')

    class Meta:
        model = LinkAccess
        fields = ('id', 'domain', 'link_id', 'url', 'case', 'name', 'referrer', 'timestamp', 'host', 'agent', 'relevant')
