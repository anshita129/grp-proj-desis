import random
import time
from decimal import Decimal
from django.core.management.base import BaseCommand
from trading.models import Stock
from trading.services import check_limit_orders


class Command(BaseCommand):
    help = 'Simulate live stock price movement'

    # allow for customization of volatility and update frequency when running the command
    def add_arguments(self, parser):
        parser.add_argument('--interval', type=int, default=5,
            help='Seconds between price updates (default: 5)')
        parser.add_argument('--volatility', type=float, default=0.02,
            help='Max % change per tick (default: 2%%)')

    # main loop that updates stock prices at regular intervals 
    def handle(self, *args, **options):
        interval   = options['interval']
        volatility = options['volatility']

        self.stdout.write(self.style.SUCCESS(
            f'Starting price simulation — updating every {interval}s'
        ))

        while True:
            stocks = Stock.objects.all()
            for stock in stocks:
                # Random % change between -volatility and +volatility
                change_pct = Decimal(str(random.uniform(-volatility, volatility)))
                change     = stock.current_price * change_pct
                new_price  = stock.current_price + change

                # Floor at ₹1 so price never goes negative
                new_price = max(new_price, Decimal('1.00'))
                new_price = round(new_price, 2)

                stock.current_price = new_price
                stock.save(update_fields=['current_price', 'last_updated'])
                #from trading.models import PriceHistory
                #PriceHistory.objects.create(stock=stock, price=new_price)

                self.stdout.write(
                    f'{stock.symbol:12} ₹{new_price:>10} '
                    f'({"+".rjust(1) if change >= 0 else ""}{round(float(change_pct)*100, 2)}%)'
                )

            # check if any limit orders can be executed at the new prices
            executed = check_limit_orders()
            if executed:
                self.stdout.write(self.style.SUCCESS(f'{executed} limit orders executed'))
            
            self.stdout.write('─' * 40)
            time.sleep(interval)