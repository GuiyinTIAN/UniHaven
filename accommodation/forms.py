from django import forms
from .models import Accommodation

class AccommodationForm(forms.ModelForm):
    address = forms.CharField(max_length=200, required=True, label="Address")

    class Meta:
        model = Accommodation

        fields = ['title', 'description', 'type', 'beds', 'bedrooms', 'price', 
                 'address', 'available_from', 'available_to', 'contact_name',
                 'contact_phone', 'contact_email',]

        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'available_from': forms.DateInput(attrs={'type': 'date'}),
            'available_to': forms.DateInput(attrs={'type': 'date'}),
            'contact_name': forms.TextInput(attrs={'placeholder': 'eg: John Doe'}),
            'contact_phone': forms.TextInput(attrs={'placeholder': 'eg: +852 1234 5678'}),
            'contact_email': forms.EmailInput(attrs={'placeholder': 'eg: your_email@example.com'}),
            'reserved': forms.CheckboxInput(attrs={'class': 'reserved-checkbox'})
        }
