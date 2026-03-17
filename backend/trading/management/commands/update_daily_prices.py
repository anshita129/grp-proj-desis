from django.core.management.base import BaseCommand
from django.utils import timezone
from trading.models import Stock, DailyStockPrice

class Command(BaseCommand):
    help = 'Updates DailyStockPrice with todays current prices for all stocks'

    def handle(self, *args, **kwargs):
        today = timezone.now().date()
        stocks = Stock.objects.all()
        updated = 0
        skipped = 0

        for stock in stocks:
            obj, created = DailyStockPrice.objects.get_or_create(
                stock=stock,
                date=today,
                defaults={
                    'close_price': stock.current_price,
                    'open_price': stock.current_price,
                    'high_price': stock.current_price,
                    'low_price': stock.current_price,
                }
            )
            if created:
                updated += 1
            else:
                # Update close price if already exists
                obj.close_price = stock.current_price
                obj.save()
                skipped += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Done! {updated} new records created, {skipped} updated for {today}'
            )
        )