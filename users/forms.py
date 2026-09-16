import re
from datetime import date

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import CustomUser, UserProfile

TEXT_INPUT_CLASSES = 'w-full border border-gray-300 rounded-sm px-3 py-2 mt-1 focus:outline-none focus:ring-2 focus:ring-javblue'
CHECKBOX_CLASSES = 'mt-1'


def _style_widgets(fields):
    for field in fields.values():
        if isinstance(field.widget, forms.CheckboxInput):
            field.widget.attrs['class'] = CHECKBOX_CLASSES
        else:
            field.widget.attrs['class'] = TEXT_INPUT_CLASSES


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _style_widgets(self.fields)
        if 'username' in self.fields:
            self.fields['username'].label = 'Correo electrónico'
            self.fields['username'].widget = forms.EmailInput(attrs={
                'class': TEXT_INPUT_CLASSES,
                'placeholder': 'nombre@ejemplo.com',
                'autocomplete': 'email',
                'id': 'id_username',
            })
        if 'password' in self.fields:
            self.fields['password'].widget.attrs.update({
                'class': TEXT_INPUT_CLASSES + ' pr-10',
                'placeholder': '••••••••',
                'autocomplete': 'current-password',
                'id': 'id_password',
            })


class SignupForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('email',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.help_text = None
        _style_widgets(self.fields)
        if 'email' in self.fields:
            self.fields['email'].widget.attrs.update({
                'placeholder': 'nombre@ejemplo.com',
                'autocomplete': 'email',
            })
        if 'password1' in self.fields:
            self.fields['password1'].widget.attrs.update({
                'class': self.fields['password1'].widget.attrs.get('class', '') + ' pr-10',
                'placeholder': '••••••••',
                'autocomplete': 'new-password',
            })
        if 'password2' in self.fields:
            self.fields['password2'].widget.attrs.update({
                'class': self.fields['password2'].widget.attrs.get('class', '') + ' pr-10',
                'placeholder': '••••••••',
                'autocomplete': 'new-password',
            })

        self.fields['email'].widget.attrs.update({
            'autocomplete': 'email',
            'autofocus': True,
            'placeholder': 'tucorreo@ejemplo.com',
        })
        # "new-password" evita que el navegador rellene aquí la contraseña de otra cuenta.
        self.fields['password1'].widget.attrs.update({'autocomplete': 'new-password'})
        self.fields['password2'].widget.attrs.update({'autocomplete': 'new-password'})


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
            'alternate_email',
            'education_level',
            'has_business',
        ]
        widgets = {
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
        }

    # Tipos de documento que en Colombia son solo numéricos.
    NUMERIC_ID_TYPES = ('CC', 'CE', 'TI')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _style_widgets(self.fields)

        self.fields['full_name'].widget.attrs.update({
            'autocomplete': 'name',
            'placeholder': 'Como aparece en tu documento',
        })
        self.fields['id_number'].widget.attrs.update({
            'inputmode': 'numeric',
            'autocomplete': 'off',
            'maxlength': '15',
        })
        self.fields['id_number'].help_text = 'Solo números, entre 6 y 10 dígitos, sin puntos ni espacios.'
        self.fields['phone'].widget.attrs.update({
            'inputmode': 'tel',
            'autocomplete': 'tel',
            'maxlength': '18',
            'placeholder': '300 123 4567',
        })
        self.fields['phone'].help_text = 'Celular de 10 dígitos (empieza por 3) o fijo de 7 dígitos.'
        self.fields['alternate_email'].widget.attrs.update({
            'autocomplete': 'email',
            'placeholder': 'Opcional, por si perdemos contacto',
        })
        self.fields['birth_date'].widget.attrs.update({
            'autocomplete': 'bday',
            'max': date.today().isoformat(),  # nadie nace mañana
        })

    def clean_id_number(self):
        """Valida según el tipo de documento elegido.

        `id_type` se declara antes que `id_number`, así que ya está limpio aquí.
        """
        numero = (self.cleaned_data.get('id_number') or '').strip()
        tipo = self.cleaned_data.get('id_type')

        if tipo in self.NUMERIC_ID_TYPES:
            if not numero.isdigit():
                raise forms.ValidationError('El número de documento debe tener solo dígitos, sin puntos ni espacios.')
            if not 6 <= len(numero) <= 10:
                raise forms.ValidationError(
                    f'El número de documento debe tener entre 6 y 10 dígitos; escribiste {len(numero)}.'
                )
        elif tipo == 'PA':
            if not re.fullmatch(r'[A-Za-z0-9]{5,15}', numero):
                raise forms.ValidationError('El pasaporte debe tener entre 5 y 15 caracteres, solo letras y números.')
        return numero

    def clean_phone(self):
        """Acepta espacios, guiones, paréntesis y prefijo +57, y guarda solo los dígitos."""
        telefono = re.sub(r'[\s()\-\.]', '', (self.cleaned_data.get('phone') or ''))
        if telefono.startswith('+57'):
            telefono = telefono[3:]
        elif telefono.startswith('+'):
            raise forms.ValidationError('Escribe un número colombiano, sin prefijo de otro país.')

        if not telefono.isdigit():
            raise forms.ValidationError('El teléfono debe tener solo números. Puedes separar con espacios o guiones, pero no usar letras.')
        if len(telefono) == 10:
            if not telefono.startswith('3'):
                raise forms.ValidationError('Un número de 10 dígitos es un celular y debe empezar por 3. Si es un fijo, escribe sus 7 dígitos.')
        elif len(telefono) != 7:
            raise forms.ValidationError(
                f'Escribe un celular de 10 dígitos o un fijo de 7; escribiste {len(telefono)} dígitos.'
            )
        return telefono
