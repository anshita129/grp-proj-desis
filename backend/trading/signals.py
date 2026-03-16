from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from trading.models import Stock, DailyStockPrice

@receiver(post_save, sender=Stock)
def save_daily_price_on_update(sender, instance, **kwargs):
    """
    Every time a Stock is saved/updated,
    automatically record today's price in DailyStockPrice
    """
    today = timezone.now().date()
    
    obj, created = DailyStockPrice.objects.update_or_create(
        stock=instance,
        date=today,
        defaults={
            'open_price': instance.current_price,
            'high_price': instance.current_price,
            'low_price': instance.current_price,
            'close_price': instance.current_price,
            'volume': 0
        }
    )