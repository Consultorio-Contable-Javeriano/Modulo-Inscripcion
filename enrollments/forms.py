from django import forms
from django.urls import reverse

from . import locations
from .models import Enrollment

TEXT_INPUT_CLASSES = 'w-full border border-gray-300 rounded-sm px-3 py-2 mt-1 focus:outline-none focus:ring-2 focus:ring-javblue'
CHECKBOX_CLASSES = 'mt-1'


class EnrollmentForm(forms.ModelForm):
    class Meta:
        model = Enrollment
        fields = [
            'entity',
            'chosen_modality',
            'city',
            'locality',
            'neighborhood',
            'data_treatment_accepted',
            'attendance_commitment',
        ]

    def __init__(self, *args, module=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.module = module
        if module is not None:
            self.fields['chosen_modality'].choices = module.allowed_modalities()
            if len(self.fields['chosen_modality'].choices) == 1:
                self.fields['chosen_modality'].initial = self.fields['chosen_modality'].choices[0][0]

        for name, field in self.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs['class'] = CHECKBOX_CLASSES
            else:
                field.widget.attrs['class'] = TEXT_INPUT_CLASSES

        self._setup_locality_field()
        self._setup_usability_hints()

    def _setup_usability_hints(self):
        """Ayudas de escritura: autocompletado del navegador y buscador de ciudad."""
        # Lista sugerida para el <datalist> que renderiza la plantilla.
        self.city_options = locations.CITIES

        self.fields['entity'].widget.attrs.update({
            'autocomplete': 'organization',
            'placeholder': 'Fundación, colegio, parroquia, empresa...',
        })
        self.fields['entity'].help_text = 'Organización por la que llegas al consultorio. Si vienes por tu cuenta, escribe "Particular".'

        self.fields['city'].widget.attrs.update({
            'list': 'lista-ciudades',
            'autocomplete': 'address-level2',
            'placeholder': 'Escribe y elige tu ciudad',
        })
        self.fields['city'].help_text = 'Escribe las primeras letras y elige de la lista. Si tu municipio no aparece, escríbelo completo.'

        self.fields['neighborhood'].widget.attrs.update({
            'autocomplete': 'address-level3',
            'placeholder': 'Barrio o vereda donde vives',
        })

    def _current_city(self):
        if self.is_bound:
            return self.data.get(self.add_prefix('city'), '')
        return self.initial.get('city') or ''

    def _setup_locality_field(self):
        """Ajusta el campo de localidad/comuna a la ciudad escrita.

        La obligatoriedad se resuelve en clean(): el campo siempre existe en el formulario
        (si no, no habria nada que intercambiar por HTMX), pero solo se exige y se muestra
        cuando la ciudad de verdad usa localidad o comuna.
        """
        city = self._current_city()
        label = locations.division_label(city)

        self.locality_label = label
        self.shows_locality = label is not None
        self.fields['locality'].required = False

        if label:
            self.fields['locality'].label = label
            self.fields['locality'].help_text = locations.division_help_text(city)

        # Al cambiar la ciudad, HTMX vuelve a pedir este campo para actualizar la etiqueta.
        self.fields['city'].widget.attrs.update({
            'hx-get': reverse('locality_field'),
            'hx-target': '#locality-field',
            'hx-swap': 'outerHTML',
            'hx-trigger': 'change, keyup changed delay:500ms',
            'hx-include': '[name=locality]',
        })

    def clean_data_treatment_accepted(self):
        accepted = self.cleaned_data['data_treatment_accepted']
        if not accepted:
            raise forms.ValidationError('Debes aceptar el tratamiento de datos para inscribirte.')
        return accepted

    def clean_attendance_commitment(self):
        commitment = self.cleaned_data['attendance_commitment']
        if not commitment:
            raise forms.ValidationError('Debes aceptar el compromiso de asistencia para inscribirte.')
        return commitment

    def clean_chosen_modality(self):
        modality = self.cleaned_data['chosen_modality']
        if self.module is not None:
            allowed = {c[0] for c in self.module.allowed_modalities()}
            if modality not in allowed:
                raise forms.ValidationError('La modalidad elegida no está disponible para este módulo.')
        return modality

    def clean(self):
        cleaned_data = super().clean()
        label = locations.division_label(cleaned_data.get('city', ''))
        locality = (cleaned_data.get('locality') or '').strip()

        if label and not locality:
            self.add_error('locality', f'Indica la {label.lower()} para completar tu ubicación.')
        elif not label:
            # La ciudad no usa localidad ni comuna: descartamos lo que hubiera quedado del
            # campo si el usuario cambió de ciudad a mitad del formulario.
            cleaned_data['locality'] = ''

        return cleaned_data
