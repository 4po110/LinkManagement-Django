from django.urls import include, path
from rest_framework import routers


from . import views

router = routers.DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'loginlogs', views.LoginViewSet)
router.register(r'links', views.LinkViewSet)
router.register(r'files', views.FileViewSet)
router.register(r'linkaccess', views.LinkAccessViewSet)
router.register(r'ipaccess', views.IPAccessViewSet)
router.register(r'domains', views.DomainViewSet)

urlpatterns = [
    path('', include(router.urls)),

]
