from django.contrib import admin

from api.models import Link, File, Domain, LinkAccess

# Register your models here.

admin.site.register(Link)
admin.site.register(File)
admin.site.register(Domain)
admin.site.register(LinkAccess)