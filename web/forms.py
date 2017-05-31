from django import forms


class EmailForm(forms.Form):
    name = forms.CharField(required=False)
    email = forms.CharField()
    comment = forms.CharField()
