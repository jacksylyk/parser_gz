from django import forms
from .models import BotKnowledge

class BotSettingsForm(forms.ModelForm):
    class Meta:
        model = BotKnowledge
        fields = ['title', 'content']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'rows': 5, 'class': 'form-control'}),
        }