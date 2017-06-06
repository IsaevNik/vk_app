from django.db import models
from django.db.models import Sum


class OrderManager(models.Manager):

    def sum_of_active_by_group(self, group):
        result = self.filter(
            donate__target__group=group, status=self.model.DEPOSITED,
            cash_send__isnull=True).aggregate(Sum('amount'))
        return result.get('amount__sum') or 0

    def sum_of_all_by_group(self, group):
        result = self.filter(donate__target__group=group,
                             status__in=[self.model.DEPOSITED, self.model.SEND]
                             ).aggregate(Sum('amount'))
        return result.get('amount__sum') or 0

    def count_of_all_by_group(self, group):
        return self.filter(donate__target__group=group,
                           status__in=[self.model.DEPOSITED, self.model.SEND]).count()


class CashSendManager(models.Manager):

    def sum_by_group(self, group, statuses):
        result = self.filter(
            wallet__group_id=group.id, status__in=statuses
        ).aggregate(Sum('amount'))
        return result.get('amount__sum') or 0
