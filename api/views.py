import os
from os import extsep
import shutil
from django.shortcuts import render
from django.db.models import Q
from django.http import Http404
from rest_framework import viewsets, mixins, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, action
from django.shortcuts import get_object_or_404
from rest_framework.serializers import Serializer
from rest_framework.parsers import FileUploadParser, MultiPartParser, FormParser
from rest_framework.views import APIView
from django.conf import settings

from authentication.models import CustomUser, LoginLog
from api.serializers import *
from api.paginations import CustomPagination
from api.models import Domain, Link, File

import json
import datetime
import io
from PIL import Image
import base64

class UserViewSet(mixins.ListModelMixin,
                mixins.RetrieveModelMixin,
                viewsets.GenericViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    permission_classes = (IsAuthenticated,)

    queryset = CustomUser.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    pagination_class = CustomPagination

    def list(self, request):
        """override"""
        users = CustomUser.objects.filter(Q(is_eliminated=False) & Q(is_admin=False) & ~Q(username='shared_user') & ~Q(username='AnonymousUser'))
        page = self.paginate_queryset(users)
        serializer = UserSerializer(page, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def retrieve(self, request, pk):
        """override"""
        user = CustomUser.objects.filter(Q(is_eliminated=False) & Q(is_admin=False) & ~Q(username='shared_user') & ~Q(username='AnonymousUser') & Q(id=pk))
        serializer = UserSerializer(user, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class LoginViewSet(mixins.ListModelMixin,
                viewsets.GenericViewSet):

    permission_classes = (IsAuthenticated,)
    queryset = LoginLog.objects.all().order_by('-user_id')
    pagination_class = CustomPagination

    def list(self, request):
        """override"""
        module = LoginLog.objects.filter(user_id=request.user.id)
        page = self.paginate_queryset(module)
        serializer = LoginSerializer(page, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class DomainViewSet(mixins.ListModelMixin,
                viewsets.GenericViewSet):

    permission_classes = (IsAuthenticated,)
    queryset = Domain.objects.all()
    pagination_class = CustomPagination

    def list(self, request):
        """override"""
        domains = Domain.objects.all()
        page = self.paginate_queryset(domains)
        serializer = DomainSerializer(page, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class LinkViewSet(mixins.CreateModelMixin,
                    mixins.ListModelMixin,
                    mixins.UpdateModelMixin,
                    mixins.DestroyModelMixin,
                    viewsets.GenericViewSet):

    permission_classes = (IsAuthenticated,)
    queryset = Link.objects.all().order_by('-user')
    serializer_class = LinkSerializer
    pagination_class = CustomPagination

    def create(self, request):
        serializer = LinkSerializer(data=request.data)
        request.data._mutable = True
        request.data['user'] = request.user.id
        domain = request.data['domain']
        case = request.data['case']
        folder = request.data['folder']
        file = request.data['file']

        try:
            link = Link.objects.get(Q(domain=domain) & Q(folder=folder))
            request.data._mutable = False
            return Response({"url": ["link with this url(domain and folder) already exists."]}, status=status.HTTP_400_BAD_REQUEST)
        except:
            domain = Domain.objects.get(Q(id=domain))
            path = f'{str(domain)}/{folder}/'
            if file != '':
                file = File.objects.get(Q(id=file))
                filename = str(file)
                filename = filename.replace(' ', '_')
                path = f'{path}{filename}'
            request.data['path'] = path
            request.data._mutable = False
            if serializer.is_valid():
                serializer.save()
                return Response(status=status.HTTP_201_CREATED)
            else:
                print("This is a bad request")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def list(self, request):
        """override"""
        links = Link.objects.filter(Q(user=request.user.id) & Q(is_active=True)).order_by('-created_date')
        page = self.paginate_queryset(links)
        serializer = LinkListSerializer(page, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def update(self, request, pk):
        query = Link.objects.filter(Q(id=pk) & Q(is_active=True))
        query.update(name=request.data['name'], case=request.data['case'])
        return Response(status=status.HTTP_205_RESET_CONTENT)

    def destroy(self, request, pk):
        query = Link.objects.filter(Q(id=pk) & Q(user=request.user.id))
        query.update(is_active=False)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False)
    def count(self, request):
        links = Link.objects.filter(Q(user=request.user.id) & Q(is_active=True))
        serializer = LinkListSerializer(links, many=True)
        json_data = json.dumps(serializer.data)
        item_dict = json.loads(json_data)
        return Response(len(item_dict), status=status.HTTP_200_OK)

class FileViewSet(mixins.CreateModelMixin,
                    mixins.ListModelMixin,
                    mixins.DestroyModelMixin,
                    viewsets.GenericViewSet):
    parser_class = (FileUploadParser,)
    permission_classes = [IsAuthenticated]
    queryset = File.objects.all().order_by('-user')
    pagination_class = CustomPagination

    def create(self, request):
        serializer = FileSerializer(data=request.data)
        request.data._mutable = True
        request.data['user'] = request.user.id
        request.data['name'] = request.data['file'].name
        request.data['type'] = self.get_type(request.data['name'])
        request.data._mutable = False

        if serializer.is_valid():
            serializer.save()
            return Response(status=status.HTTP_201_CREATED)
        else:
            print("This is a bad request")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def list(self, request):
        try:
            shared_user = CustomUser.objects.get(username="shared_user")
        except:
            raise Http404("There is no shared user.")
        query = File.objects.filter(Q(user=request.user.id) | Q(user=shared_user.id)).order_by('-date_created')
        page = self.paginate_queryset(query)
        serializer = FileListSerializer(page, many=True)
        json_data = json.dumps(serializer.data)
        item_dict = json.loads(json_data)
        data = []
        for item in item_dict:
            filename = settings.MEDIA_ROOT + '/' + item['file']
            item['size'] = os.path.getsize(filename)
            if item['type'] in ['PNG', 'JPG']:
                output = io.BytesIO()
                img = Image.open(filename)
                img.thumbnail((128, 128))
                img.save(output, format='PNG')
                file_data = base64.b64encode(output.getvalue())
                file_data = file_data.decode('ascii')
                item['thumbnail'] = file_data
            data.append(item)
        return Response(data, status=status.HTTP_200_OK)

    @action(detail=False)
    def count(self, request):
        try:
            shared_user = CustomUser.objects.get(username="shared_user")
        except:
            raise Http404("There is no shared user.")
        query = File.objects.filter(Q(user=request.user.id) | Q(user=shared_user.id))
        serializer = FileListSerializer(query, many=True)
        json_data = json.dumps(serializer.data)
        item_dict = json.loads(json_data)
        return Response(len(item_dict), status=status.HTTP_200_OK)

    def destroy(self, request, pk):
        query = File.objects.filter(Q(id=pk) & Q(user=request.user.id))
        query.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_type(self, string):
        ext = string[-4:].upper()
        if ext in ['.PDF', '.DOC', '.JPG', '.PNG']:
            return ext[1:]
        return 'UNKNOWN'

class LinkAccessViewSet(mixins.ListModelMixin,
                mixins.RetrieveModelMixin,
                mixins.UpdateModelMixin,
                viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    queryset = LinkAccess.objects.all().order_by('-link')
    pagination_class = CustomPagination

    def list(self, request):
        """override"""
        access = LinkAccess.objects.filter(Q(user=request.user.id)).order_by('-timestamp')
        page = self.paginate_queryset(access)
        serializer = AccessSerializer(page, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def retrieve(self, request, pk):
        """override"""
        relevant = self.request.query_params.get('relevant')
        if relevant == 'true':
            relevant = True
        elif relevant == 'false':
            relevant = False
        else:
            relevant = None
            
        if relevant is None:
            access = LinkAccess.objects.filter(Q(user=request.user.id) & Q(link=pk)).order_by('-timestamp')
        else:
            access = LinkAccess.objects.filter(Q(user=request.user.id) & Q(link=pk) &Q(relevant=relevant)).order_by('-timestamp')
        page = self.paginate_queryset(access)
        serializer = AccessSerializer(page, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def update(self, request, pk):
        query = LinkAccess.objects.filter(Q(user=request.user.id) & Q(id=pk))
        query = query.update(relevant=request.data['relevant'])
        if query:
            return Response(status=status.HTTP_205_RESET_CONTENT)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False)
    def count(self, request):
        link = self.request.query_params.get('link_id')
        
        relevant = self.request.query_params.get('relevant')
        if relevant == 'true':
            relevant = True
        elif relevant == 'false':
            relevant = False
        else:
            relevant = None

        if link is None and relevant is None:
            access = LinkAccess.objects.filter(Q(user=request.user.id))
        elif relevant is None:
            access = LinkAccess.objects.filter(Q(user=request.user.id) & Q(link=link))
        elif link is None:
            access = LinkAccess.objects.filter(Q(user=request.user.id) & Q(relevant=relevant))
        else:
            access = LinkAccess.objects.filter(Q(user=request.user.id) & Q(relevant=relevant) & Q(link=link))
        serializer = AccessSerializer(access, many=True)
        json_data = json.dumps(serializer.data)
        item_dict = json.loads(json_data)
        return Response(len(item_dict), status=status.HTTP_200_OK)

    @action(detail=False)
    def accessforamonth(self, request):
        link = self.request.query_params.get('link_id')
        if link is None:
            access = LinkAccess.objects.filter(Q(user=request.user.id))
        else:
            access = LinkAccess.objects.filter(Q(user=request.user.id) & Q(link=link))
        serializer = AccessSerializer(access, many=True)
        json_data = json.dumps(serializer.data)
        item_dict = json.loads(json_data)
        start_date = datetime.datetime.now() - datetime.timedelta(29)
        data = {}
        for i in range(30):
            date = datetime.datetime.date(start_date + datetime.timedelta(i))
            data[str(date)] = 0
        for item in item_dict:
            #"2021-06-05T08:06:15.325568+02:00"
            date_point = datetime.datetime.date(datetime.datetime.strptime(item['timestamp'].split("T")[0], '%Y-%m-%d'))
            if date_point < datetime.datetime.date(start_date):
                continue
            data[str(date_point)] += 1
        return Response([data], status=status.HTTP_200_OK)

    @action(detail=False)
    def lastaccesses(self, request):
        access = LinkAccess.objects.filter(Q(user=request.user.id))
        serializer = AccessSerializer(access, many=True)
        json_data = json.dumps(serializer.data)
        item_dict = json.loads(json_data)
        # item_dict = item_dict[::-1]
        if len(item_dict) > 20:
            item_dict = item_dict[-20:]
        data = []
        for item in item_dict:
            link = Link.objects.get(Q(path=item['url']))
            if not link.is_active:
                continue
            item['link_id'] = link.id
            item['name'] = link.name
            item['case'] = link.case
            data.append(item)
        return Response(data, status=status.HTTP_200_OK)

    @action(detail=False)
    def linkforamonth(self, request):
        access = LinkAccess.objects.filter(Q(user=request.user.id))
        serializer = AccessSerializer(access, many=True)
        json_data = json.dumps(serializer.data)
        item_dict = json.loads(json_data)
        path = {}
        data = {}
        start_date = datetime.datetime.now() - datetime.timedelta(29)
        for i in range(30):
            date = datetime.datetime.date(start_date + datetime.timedelta(i))
            path[str(date)] = []
            data[str(date)] = 0
        for item in item_dict:
            date_point = datetime.datetime.date(datetime.datetime.strptime(item['timestamp'].split("T")[0], '%Y-%m-%d'))
            if str(date_point) in path:
                if item['url'] in path[str(date_point)] or date_point < datetime.datetime.date(start_date):
                    continue
                path[str(date_point)].append(item['url'])
                data[str(date_point)] += 1
        return Response([data], status=status.HTTP_200_OK)

    @action(detail=False)
    def accessperlink(self, request):
        access = LinkAccess.objects.filter(Q(user=request.user.id))
        serializer = AccessSerializer(access, many=True)
        json_data = json.dumps(serializer.data)
        item_dict = json.loads(json_data)
        data = {}
        for item in item_dict:
            if not item['url'] in data:
                data[item['url']] = 1
            else:
                data[item['url']] += 1
        result = []
        for url in data:
            item = {}
            link = Link.objects.get(Q(path=url))
            if not link.is_active:
                continue
            item['id'] = link.id
            item['name'] = link.name
            item['url'] = url
            item['count'] = data[url]
            result.append(item)

        return Response(result, status=status.HTTP_200_OK)

    @action(detail=True)
    def infolink(self, request, pk):
        access = LinkAccess.objects.filter(Q(user=request.user.id) & Q(link=pk))
        link = Link.objects.filter(Q(id=pk))
        link = LinkListSerializer(link, many=True).data
        serializer = AccessSerializer(access, many=True)
        json_data = json.dumps(serializer.data)
        item_dict = json.loads(json_data)
        numaccess = len(item_dict)
        date = None
        for item in item_dict:
            date = item['timestamp']
        json_data = json.dumps(link)
        item_dict = json.loads(json_data)
        data = {}
        for item in item_dict:
            data = item
            data['last_date'] = date
            data['accesses'] = numaccess
        return Response([data], status=status.HTTP_200_OK)


class IPAccessViewSet(mixins.ListModelMixin,
                    viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    queryset = LinkAccess.objects.all().order_by('-host')
    pagination_class = CustomPagination

    def list(self, request):
        """override"""
        host = self.request.query_params.get('host')
        relevant = self.request.query_params.get('relevant')
        if relevant == 'true':
            relevant = True
        elif relevant == 'false':
            relevant = False
        else:
            relevant = None

        if host is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        if relevant is None:
            access = LinkAccess.objects.filter(Q(user=request.user.id) & Q(host=host)).order_by('-timestamp')
        else:
            access = LinkAccess.objects.filter(Q(user=request.user.id) & Q(host=host) & Q(relevant=relevant)).order_by('-timestamp')
        page = self.paginate_queryset(access)
        serializer = AccessSerializer(page, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False)
    def count(self, request):
        host = self.request.query_params.get('host')
        relevant = self.request.query_params.get('relevant')
        if relevant == 'true':
            relevant = True
        elif relevant == 'false':
            relevant = False
        else:
            relevant = None

        if host is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        if relevant is None:
            access = LinkAccess.objects.filter(Q(user=request.user.id) & Q(host=host))
        else:
            access = LinkAccess.objects.filter(Q(user=request.user.id) & Q(host=host) &Q(relevant=relevant))
        serializer = AccessSerializer(access, many=True)
        json_data = json.dumps(serializer.data)
        item_dict = json.loads(json_data)
        numaccess = len(item_dict)
        return Response([numaccess], status=status.HTTP_200_OK)

    @action(detail=False)
    def countperday(self, request):
        host = self.request.query_params.get('host')
        if host is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        access = LinkAccess.objects.filter(Q(user=request.user.id) & Q(host=host))
        serializer = AccessSerializer(access, many=True)
        json_data = json.dumps(serializer.data)
        item_dict = json.loads(json_data)
        data = {}
        for item in item_dict:
            date_point = datetime.datetime.date(datetime.datetime.strptime(item['timestamp'].split("T")[0], '%Y-%m-%d'))
            if not str(date_point) in data:
                data[str(date_point)] = 1
            else:
                data[str(date_point)] += 1
        return Response([data], status=status.HTTP_200_OK)
