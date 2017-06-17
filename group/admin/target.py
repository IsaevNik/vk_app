from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError

from group.models import Group
from group.models import Target


class TargetForm(forms.ModelForm):
    class Meta:
        model = Target
        fields = '__all__'

    def clean(self):
        if self.current_user:
            if not self.cleaned_data['amount']:
                raise ValidationError('Поле <сумма> - обязательно для заполнения')
        return self.cleaned_data


class TargetAdmin(admin.ModelAdmin):
    fields = ['name', 'description', 'group', 'amount', 'active']
    list_display = ('__str__', 'amount', 'donates_sum', 'active')
    list_editable = ('active', )
    form = TargetForm

    def get_queryset(self, request):
        if request.user.is_superuser:
            return Target.objects.all()
        target = Target.objects.values('id').filter(
            group__admin=request.user).first()
        return Target.objects.filter(group__admin=request.user).exclude(id=target['id'])

    def get_form(self, request, *args, **kwargs):
        form = super().get_form(request, *args, **kwargs)
        if not request.user.is_superuser:
            form.current_user = request.user
            form.base_fields['group'].queryset = Group.objects.filter(admin=request.user)
        return form

    def get_actions(self, request):
        actions = super().get_actions(request)
        if not request.user.is_superuser:
            del actions['delete_selected']
        return actions
