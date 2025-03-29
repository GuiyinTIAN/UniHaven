from django import forms
from .models import Accommodation

class AccommodationForm(forms.ModelForm):
    address = forms.CharField(max_length=200, required=True, label="Address")

    class Meta:
        model = Accommodation
        fields = ['title', 'description', 'type', 'beds', 'bedrooms', 'price', 'address']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }
