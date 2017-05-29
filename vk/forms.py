from django import forms


class DonateForm(forms.Form):
    amount = forms.IntegerField()
    comment = forms.CharField(required=False)
