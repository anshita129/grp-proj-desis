from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from trading.models import Stock, DailyStockPrice, Wallet
from django.conf import settings
from django.core.management import call_command
from django.contrib.auth import get_user_model

User = get_user_model()

@receiver(post_save, sender=User)
def setup_new_user(sender, instance, created, **kwargs):
    if created:
        try:
            from trading.models import Wallet, Stock
            from decimal import Decimal
            
            # Create wallet if doesn't exist
            Wallet.objects.get_or_create(
                student=instance,
                defaults={'balance': Decimal('100000.00')}
            )
        except Exception as e:
            print(f"Error setting up new user: {e}")

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