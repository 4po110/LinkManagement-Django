# Create your views here.
from rest_framework import status
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

from django.utils import timezone
from django.db.models import Q

from authentication.models import LoginLog, CustomUser
from authentication.serializers import *

from api.paginations import *

import logging

error_log=logging.getLogger('error')

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            raise InvalidToken(e.args[0])

        try:
            login_logout_logs = LoginLog.objects.filter(session_key=request.session.session_key, user=serializer.validated_data['user_id'])[:1]
            if not login_logout_logs:
                user = CustomUser.objects.get(Q(id=serializer.validated_data['user_id']))
                login_logout_log = LoginLog(login_time=timezone.now(),session_key=request.session.session_key, user=user, host=visitor_ip_address(request))
                login_logout_log.save()
        except Exception as e:
            # log the error
            error_log.error("log_user_logged_in request: %s, error: %s" % (request, e))

        return Response(serializer.validated_data, status=status.HTTP_200_OK)

def visitor_ip_address(request):

    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')

    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
