from django import forms

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
