import re

from django.contrib import admin
from django.core.exceptions import ValidationError
from django import forms

from group.models import Wallet


class WalletForm(forms.ModelForm):
    class Meta:
        model = Wallet
        fields = '__all__'

    def clean(self):
        currency = self.cleaned_data.get('currency')
        purse = self.cleaned_data.get('purse')
        if currency == Wallet.YD:
            reg = re.compile(r'^(\d){15}$')
            if not reg.match(purse):
                raise ValidationError('Для яндекс денег требуется следующий формат: <410011729822xxx>')
        elif currency == Wallet.QIWI:
            reg = re.compile(r'^\+7(\d){10}$')
            if not reg.match(purse):
                raise ValidationError('Для QIWI требуется следующий формат: <+7910123xxxx>')
        else:
            reg = re.compile(r'^(\d){16}\s(\d){2}/(\d){2}$')
            if not reg.match(purse):
                raise ValidationError('Для VISA требуется следующий формат: <123456789123xxxx 01/01>')
        return self.cleaned_data


class WalletAdmin(admin.ModelAdmin):

    form = WalletForm

    def get_queryset(self, request):
        if request.user.is_superuser:
            return Wallet.objects.all()
        return Wallet.objects.filter(group__admin=request.user)

    def get_actions(self, request):
        actions = super().get_actions(request)
        if not request.user.is_superuser:
            del actions['delete_selected']
        return actions

    def get_fields(self, request, obj=None):
        fields = super().get_fields(request)
        if not request.user.is_superuser:
            fields.remove('group')
        return fields
