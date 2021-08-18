from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser
from .forms import CustomUserForm

# Register your models here.

class AccountAdmin(UserAdmin):
    form = CustomUserForm
    list_display = ('username', 'email', 'date_joined', 'last_login', 'is_admin', 'is_staff', 'is_eliminated', 'date_eliminated')
    search_fields = ('username', 'email',)
    readonly_fields = ('date_joined', 'last_login')
    ordering = ('-date_joined', )
    filter_horizontal = ()
    list_filter = ()
    fieldsets = ()
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2'),
        }),
    )

admin.site.register(CustomUser, AccountAdmin)