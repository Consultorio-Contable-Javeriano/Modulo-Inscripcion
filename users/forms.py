from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import CustomUser, UserProfile

TEXT_INPUT_CLASSES = 'w-full border border-gray-300 rounded-sm px-3 py-2 mt-1 focus:outline-none focus:ring-2 focus:ring-javblue'
CHECKBOX_CLASSES = 'mt-1'


def _style_widgets(fields):
    for field in fields.values():
        if isinstance(field.widget, forms.CheckboxInput):
            field.widget.attrs['class'] = CHECKBOX_CLASSES
        else:
            field.widget.attrs['class'] = TEXT_INPUT_CLASSES


class SignupForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('email',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.help_text = None
        _style_widgets(self.fields)


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = [
            'full_name',
            'id_type',
            'id_number',
            'birth_date',
            'gender',
            'phone',
            'education_level',
            'has_business',
        ]
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _style_widgets(self.fields)
