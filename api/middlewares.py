from .models import LinkAccess, Link
from authentication.models import CustomUser
from django.shortcuts import redirect
from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from django.http import HttpResponseNotFound, HttpResponse
import json
import base64

class AccessLogsMiddleware(object):

    def __init__(self, get_response=None):
        self.get_response = get_response
        # One-time configuration and initialization.

    def __call__(self, request):
        # create session
        if not request.session.session_key:
            request.session.create()

        domain = request.get_host()
        if domain == 'localhost' or domain == '127.0.0.1' or domain == '62.171.162.191':
            response = self.get_response(request)
            return response

        if request.method == "POST":
            response = self.get_response(request)
            return HttpResponseNotFound('<h1>Page not found</h1>')
        try:
            link = Link.objects.get(Q(is_active=True) & (Q(path=f'{domain}{request.path}') | Q(path=f'{domain}{request.path}/')))
        except:
            return HttpResponseNotFound('<h1>Page not found</h1>')

        access_logs_data = dict()

        user = link.user

        access_logs_data['user'] = user
        access_logs_data["link"] = link
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        access_logs_data["host"] = x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')
        access_logs_data["referrer"] = request.META.get('HTTP_REFERER',None)
        access_logs_data["agent"] = request.META['HTTP_USER_AGENT']
        access_logs_data["timestamp"] = timezone.now()

        try:
            LinkAccess(**access_logs_data).save()
        except Exception as e:
            pass

        if link.file == None:
            return HttpResponse('<h1></h1>')

        filepath = settings.MEDIA_ROOT + '/' + str(link.file.file)

        if link.file.type == 'DOC':
            content_type = 'application/msword'
        elif link.file.type == 'PDF':
            content_type = 'application/pdf'
        elif link.file.type == 'JPG':
            content_type = 'image/jpeg'
        elif link.file.type == 'PNG':
            content_type = 'image/png'
        else:
            content_type = 'application/octet-stream'

        try:
            with open(filepath, 'rb') as f:
                file_data = f.read()

            if 'image' in content_type:
                file_data = base64.b64encode(file_data)
                file_data = file_data.decode('ascii')
                html = f"""
                        <!DOCTYPE html>
                        <html>
                        <head>
                        <meta name="viewport" content="width=device-width, initial-scale=1">
                        </head>
                        <body>
                        <script>
                            var img = document.createElement('img');
                            img.src = 'data:image/jpeg;base64,{file_data}';
                            document.body.appendChild(img);
                        </script>
                        </body>
                        </html>
                    """
                response = HttpResponse(html)
            else:
                response = HttpResponse(file_data, content_type=content_type)
                response['Content-Disposition'] = f'attachment; filename={link.file.name}'

        except IOError:
            # handle file not exist case here
            response = HttpResponseNotFound('<h1>File not exist</h1>')

        return response
