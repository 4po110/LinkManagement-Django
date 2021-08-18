from .models import CustomUser
from django import forms
from django.utils import timezone

class CustomUserForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = '__all__'

    def clean(self):
        is_eliminated = self.cleaned_data.get('is_eliminated', False)
        if is_eliminated:
            self.cleaned_data['date_eliminated'] = timezone.now()
        else:
            self.cleaned_data['date_eliminated'] = None
        return self.cleaned_data