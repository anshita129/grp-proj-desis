from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import random
from trading.models import Stock, StockPriceCandle
from .simulate_prices import CANDLE_INTERVAL_MINUTES, SECTOR_VOLATILITY
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Seeds 1 hour of historical 1m candles for all stocks.'

    # clear the db to avoid any random spikes in the graph 
    def add_arguments(self, parser):
            parser.add_argument(
                '--clear',
                action='store_true',  # True if flag is passed, False otherwise
                help='Clear all existing candles before seeding new ones',
            )

    def handle(self, *args, **options):
        if options['clear']:
            # clear full table 
            self.stdout.write("Clearing existing candles from the database...")
            deleted_count, _ = StockPriceCandle.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"Deleted {deleted_count} old candles."))

        self.stdout.write("Starting to seed candles...")
        seed_historical_candles()
        self.stdout.write(self.style.SUCCESS("Successfully seeded candles!"))

def seed_historical_candles():
    """
    Seeds 1 hour of historical 1m candles for all stocks.
    """
    
    now = timezone.now().replace(second=0, microsecond=0)
    now = now.replace(minute=(now.minute // CANDLE_INTERVAL_MINUTES) * CANDLE_INTERVAL_MINUTES)
    
    stocks = Stock.objects.all()
    total = 0
    stocks_to_update = []

    for stock in stocks:
        volatility = SECTOR_VOLATILITY.get(stock.sector, SECTOR_VOLATILITY['default'])
        
        candles = []
        price = Decimal(str(stock.current_price))
        
        # Generate 60 candles chronologically (from T-60 up to T-1)
        for i in range(60, 0, -1):
            timestamp = now - timedelta(minutes=i)
            
            open_price = price
            high = price
            low = price
            
            ticks = 12 
            for _ in range(ticks):
                change_pct = Decimal(str(random.uniform(-volatility, volatility)))
                change_pct += Decimal('0.0001') 
                price = price * (1 + change_pct)
                price = max(price, Decimal('1.00'))
                price = round(price, 2)
                
                high = max(high, price)
                low = min(low, price)
            
            close_price = price
            
            candles.append(StockPriceCandle(
                stock=stock,
                timestamp=timestamp,
                interval=f"{CANDLE_INTERVAL_MINUTES}m",
                open_price=open_price,
                high_price=high,
                low_price=low,
                close_price=close_price,
            ))
        
        StockPriceCandle.objects.bulk_create(candles, ignore_conflicts=True)
        total += len(candles)
        
        # Update the stock's current price so the live feed connects smoothly
        stock.current_price = price
        stocks_to_update.append(stock)
        
        print(f"  seeded {stock.symbol}: {len(candles)} candles, final price ₹{price}")
    
    # Bulk update all stock prices at the end
    if stocks_to_update:
        Stock.objects.bulk_update(stocks_to_update, ['current_price'])
        
    print(f"\nDone - {total} candles seeded across {stocks.count()} stocks")