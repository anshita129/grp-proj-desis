from django.core.management.base import BaseCommand
from users.models import User
from trading.models import Stock, Wallet
from decimal import Decimal

STOCKS = [
    ('RELIANCE', 'Reliance Industries', 'Energy',     2850.00),
    ('TCS',      'Tata Consultancy',    'IT',          3920.00),
    ('INFY',     'Infosys',             'IT',          1780.00),
    ('HDFC',     'HDFC Bank',           'Banking',     1650.00),
    ('WIPRO',    'Wipro Limited',       'IT',           480.00),
    ('SBIN',     'State Bank of India', 'Banking',      820.00),
    ('BAJFINANCE','Bajaj Finance',      'NBFC',        7200.00),
]

class Command(BaseCommand):
    help = 'Seed stocks and create wallets for all users'

    def handle(self, *args, **kwargs):
        # seed stocks from the predefined list, using update_or_create to avoid duplicates if run multiple times
        for symbol, name, sector, price in STOCKS:
            Stock.objects.update_or_create(
                symbol=symbol,
                defaults={'company_name': name, 'sector': sector, 'current_price': price}
            )
        self.stdout.write(self.style.SUCCESS(f'Seeded {len(STOCKS)} stocks'))

        # create wallets for all existing users if they don't already have one
        for user in User.objects.all():
            Wallet.objects.get_or_create(
                student=user,
                defaults={'balance': Decimal('100000.00')}
            )
        self.stdout.write(self.style.SUCCESS('Wallets created'))