import random
import time
from decimal import Decimal
from django.core.management.base import BaseCommand
from trading.models import Stock
from trading.services import check_limit_orders
from django.core.cache import cache


# Different sectors move differently in real markets
# High volatility: Tech, Crypto-adjacent, Small caps
# Low volatility: FMCG, Pharma, Utilities
SECTOR_VOLATILITY = {
    'IT':           0.025,   # tech stocks move more
    'Tech':         0.030,   # new-age tech even more
    'Banking':      0.018,
    'NBFC':         0.022,
    'Energy':       0.020,
    'FMCG':         0.010,   # stable consumer goods
    'Auto':         0.022,
    'Pharma':       0.015,
    'Healthcare':   0.015,
    'Metals':       0.030,   # metals are volatile
    'Cement':       0.015,
    'Telecom':      0.018,
    'Consumer':     0.014,
    'Retail':       0.022,
    'Insurance':    0.012,
    'Conglomerate': 0.020,
    'Industrial':   0.018,
    'Real Estate':  0.025,
    'Aviation':     0.030,   # airlines are very volatile
    'Services':     0.018,
    'Construction': 0.020,
    'default':      0.020,   # fallback for unknown sectors
}

# Stocks tend to drift slightly upward over time (market bias)
# This adds a tiny positive nudge to simulate a bull market
MARKET_DRIFT = Decimal('0.0001')

class Command(BaseCommand):
    help = 'Simulate live stock price movement with sector-based volatility'

    def add_arguments(self, parser):
        parser.add_argument('--interval', type=int, default=5,
            help='Seconds between price updates (default: 5)')
        parser.add_argument('--volatility', type=float, default=None,
            help='Override volatility for all sectors (default: sector-based)')
        parser.add_argument('--drift', action='store_true', default=True,
            help='Apply slight upward market drift (default: True)')
        parser.add_argument('--no-drift', dest='drift', action='store_false',
            help='Disable upward market drift')
        #parser.add_argument('--no-history', action='store_true', default=False,
        #    help='Skip writing to PriceHistory table (faster for testing)')

    def handle(self, *args, **options):
        interval        = options['interval']
        vol_override    = options['volatility']
        apply_drift     = options['drift']
        #skip_history    = options['no_history']

        self.stdout.write(self.style.SUCCESS(
            f'Price simulation started — every {interval}s | '
            f'drift={"on" if apply_drift else "off"} | '
           # f'history={"off" if skip_history else "on"}'
        ))

        tick = 0  # track number of updates for logging

        while True:
            tick += 1
            stocks = Stock.objects.all()

            # Occasionally simulate a market-wide event
            # 2% chance per tick of a broad market move (±0.5%)
            market_shock = Decimal('0')
            if random.random() < 0.02:
                market_shock = Decimal(str(random.uniform(-0.005, 0.005)))
                direction    = "UP" if market_shock > 0 else "DOWN"
                self.stdout.write(self.style.WARNING(
                    f' Market event — broad {direction} move ({round(float(market_shock)*100, 3)}%)'
                ))

            # price_history_bulk = []  # batch inserts for performance

            for stock in stocks:
                # Get volatility for this sector
                volatility = vol_override if vol_override else \
                    SECTOR_VOLATILITY.get(stock.sector, SECTOR_VOLATILITY['default'])

                # Random price change for this stock
                change_pct = Decimal(str(random.uniform(-volatility, volatility)))

                # Add market-wide shock if there is one
                change_pct += market_shock

                # Add slight upward drift to simulate bull market
                if apply_drift:
                    change_pct += MARKET_DRIFT

                change    = stock.current_price * change_pct
                new_price = stock.current_price + change

                # Floor at ₹1 — price can never go negative or zero
                new_price = max(new_price, Decimal('1.00'))
                new_price = round(new_price, 2)

                old_price = stock.current_price
                stock.current_price = new_price
                stock.save(update_fields=['current_price', 'last_updated'])
                cache.set(f'prev_close_{stock.symbol}', float(old_price), timeout=None) 


                # Prepare price history entry for bulk insert
                #if not skip_history:
                #    price_history_bulk.append(
                #        PriceHistory(stock=stock, price=new_price)
                #    )

                # Console output — show arrow direction and % change
                arrow      = "↑" if new_price >= old_price else "↓"
                change_str = f'{round(float(change_pct) * 100, 2):+.2f}%'
                self.stdout.write(
                    f'{arrow} {stock.symbol:14} ₹{new_price:>10} {change_str:>8}  [{stock.sector}]'
                )

                # Bulk insert all price history in one DB call — much faster than one by one
                # if not skip_history and price_history_bulk:
                #    PriceHistory.objects.bulk_create(price_history_bulk)

            # Check if any limit orders can now be executed at new prices
            try:
                executed = check_limit_orders()
            except Exception as e:
                self.stdout.write(f'check_limit_orders ERROR: {e}')
                executed = 0
            if executed:
                self.stdout.write(self.style.SUCCESS(
                    f' {executed} limit order(s) executed'
                ))


            self.stdout.write(f'{"─" * 60}  tick #{tick}')

            #self.stdout.write(
            #    f'{"─" * 60}  tick #{tick} | {len(price_history_bulk)} prices recorded'
            #)
            time.sleep(interval)