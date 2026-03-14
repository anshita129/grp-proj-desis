from django.core.management.base import BaseCommand
from users.models import User
from trading.models import Stock, Wallet
from decimal import Decimal

# Full Nifty 50 + popular additional stocks grouped by sector
# Prices are approximate, simulate_prices will update them live
STOCKS = [
    # ── IT ────────────────────────────────────────────────────────────────────
    ('TCS',         'Tata Consultancy Services',    'IT',           3920.00),
    ('INFY',        'Infosys',                      'IT',           1780.00),
    ('WIPRO',       'Wipro Limited',                'IT',            480.00),
    ('HCLTECH',     'HCL Technologies',             'IT',           1620.00),
    ('TECHM',       'Tech Mahindra',                'IT',           1290.00),
    ('LTIM',        'LTIMindtree',                  'IT',           5800.00),
    ('MPHASIS',     'Mphasis',                      'IT',           2800.00),
    ('PERSISTENT',  'Persistent Systems',           'IT',           5200.00),

    # ── Banking ───────────────────────────────────────────────────────────────
    ('HDFCBANK',    'HDFC Bank',                    'Banking',      1650.00),
    ('ICICIBANK',   'ICICI Bank',                   'Banking',      1180.00),
    ('SBIN',        'State Bank of India',          'Banking',       820.00),
    ('KOTAKBANK',   'Kotak Mahindra Bank',          'Banking',      1900.00),
    ('AXISBANK',    'Axis Bank',                    'Banking',      1150.00),
    ('INDUSINDBK',  'IndusInd Bank',                'Banking',      1450.00),
    ('BANKBARODA',  'Bank of Baroda',               'Banking',       280.00),
    ('PNB',         'Punjab National Bank',         'Banking',       120.00),
    ('CANBK',       'Canara Bank',                  'Banking',       110.00),

    # ── NBFC & Finance ────────────────────────────────────────────────────────
    ('BAJFINANCE',  'Bajaj Finance',                'NBFC',         7200.00),
    ('BAJAJFINSV',  'Bajaj Finserv',                'NBFC',         1820.00),
    ('CHOLAFIN',    'Cholamandalam Investment',     'NBFC',         1380.00),
    ('MUTHOOTFIN',  'Muthoot Finance',              'NBFC',         2100.00),

    # ── Energy & Oil ──────────────────────────────────────────────────────────
    ('RELIANCE',    'Reliance Industries',          'Energy',       2850.00),
    ('ONGC',        'Oil & Natural Gas Corp',       'Energy',        280.00),
    ('POWERGRID',   'Power Grid Corporation',       'Energy',        320.00),
    ('NTPC',        'NTPC Limited',                 'Energy',        380.00),
    ('COALINDIA',   'Coal India',                   'Energy',        480.00),
    ('IOC',         'Indian Oil Corporation',       'Energy',        180.00),
    ('BPCL',        'Bharat Petroleum',             'Energy',        380.00),
    ('ADANIGREEN',  'Adani Green Energy',           'Energy',        980.00),
    ('TATAPOWER',   'Tata Power',                   'Energy',        480.00),

    # ── FMCG ──────────────────────────────────────────────────────────────────
    ('HINDUNILVR',  'Hindustan Unilever',           'FMCG',         2650.00),
    ('ITC',         'ITC Limited',                  'FMCG',          470.00),
    ('NESTLEIND',   'Nestle India',                 'FMCG',        24500.00),
    ('BRITANNIA',   'Britannia Industries',         'FMCG',         5200.00),
    ('DABUR',       'Dabur India',                  'FMCG',          620.00),
    ('MARICO',      'Marico Limited',               'FMCG',          680.00),
    ('GODREJCP',    'Godrej Consumer Products',     'FMCG',         1380.00),
    ('COLPAL',      'Colgate-Palmolive India',      'FMCG',         3200.00),

    # ── Auto ──────────────────────────────────────────────────────────────────
    ('MARUTI',      'Maruti Suzuki India',          'Auto',        12800.00),
    ('TATAMOTORS',  'Tata Motors',                  'Auto',          980.00),
    ('M&M',         'Mahindra & Mahindra',          'Auto',         2980.00),
    ('BAJAJ-AUTO',  'Bajaj Auto',                   'Auto',         9800.00),
    ('HEROMOTOCO',  'Hero MotoCorp',                'Auto',         4800.00),
    ('EICHERMOT',   'Eicher Motors',                'Auto',         4800.00),
    ('TVSMOTOR',    'TVS Motor Company',            'Auto',         2400.00),
    ('ASHOKLEY',    'Ashok Leyland',                'Auto',          240.00),

    # ── Pharma & Healthcare ───────────────────────────────────────────────────
    ('SUNPHARMA',   'Sun Pharmaceutical',           'Pharma',       1780.00),
    ('DRREDDY',     "Dr Reddy's Laboratories",      'Pharma',       6800.00),
    ('CIPLA',       'Cipla Limited',                'Pharma',       1650.00),
    ('DIVISLAB',    "Divi's Laboratories",          'Pharma',       4800.00),
    ('BIOCON',      'Biocon Limited',               'Pharma',        380.00),
    ('AUROPHARMA',  'Aurobindo Pharma',             'Pharma',       1280.00),
    ('APOLLOHOSP',  'Apollo Hospitals',             'Healthcare',   7200.00),
    ('MAXHEALTH',   'Max Healthcare',               'Healthcare',    980.00),

    # ── Metals & Mining ───────────────────────────────────────────────────────
    ('TATASTEEL',   'Tata Steel',                   'Metals',        180.00),
    ('HINDALCO',    'Hindalco Industries',          'Metals',        680.00),
    ('JSWSTEEL',    'JSW Steel',                    'Metals',        980.00),
    ('SAIL',        'Steel Authority of India',     'Metals',        140.00),
    ('VEDL',        'Vedanta Limited',              'Metals',        480.00),
    ('NMDC',        'NMDC Limited',                 'Metals',        280.00),

    # ── Cement & Construction ─────────────────────────────────────────────────
    ('ULTRACEMCO',  'UltraTech Cement',             'Cement',      11800.00),
    ('GRASIM',      'Grasim Industries',            'Cement',       2780.00),
    ('SHREECEM',    'Shree Cement',                 'Cement',      28000.00),
    ('AMBUJACEM',   'Ambuja Cements',               'Cement',        680.00),
    ('ACC',         'ACC Limited',                  'Cement',       2400.00),
    ('LT',          'Larsen & Toubro',              'Construction', 3680.00),

    # ── Telecom ───────────────────────────────────────────────────────────────
    ('BHARTIARTL',  'Bharti Airtel',                'Telecom',      1680.00),
    ('IDEA',        'Vodafone Idea',                'Telecom',         18.00),

    # ── Consumer & Retail ─────────────────────────────────────────────────────
    ('TITAN',       'Titan Company',                'Consumer',     3680.00),
    ('ASIANPAINT',  'Asian Paints',                 'Consumer',     2980.00),
    ('DMART',       'Avenue Supermarts (DMart)',    'Retail',       4980.00),
    ('TRENT',       'Trent Limited',                'Retail',       7200.00),
    ('NYKAA',       'FSN E-Commerce (Nykaa)',       'Retail',        220.00),
    ('ZOMATO',      'Zomato Limited',               'Tech',          280.00),
    ('PAYTM',       'One97 Communications',         'Tech',          980.00),

    # ── Insurance ─────────────────────────────────────────────────────────────
    ('HDFCLIFE',    'HDFC Life Insurance',          'Insurance',     680.00),
    ('SBILIFE',     'SBI Life Insurance',           'Insurance',    1680.00),
    ('ICICIGI',     'ICICI Lombard General Ins.',   'Insurance',    1980.00),

    # ── Conglomerate & Industrial ─────────────────────────────────────────────
    ('ADANIENT',    'Adani Enterprises',            'Conglomerate', 2980.00),
    ('ADANIPORTS',  'Adani Ports & SEZ',            'Conglomerate', 1380.00),
    ('SIEMENS',     'Siemens India',                'Industrial',   7800.00),
    ('ABB',         'ABB India',                    'Industrial',   8200.00),
    ('HAVELLS',     'Havells India',                'Industrial',   1980.00),

    # ── Real Estate ───────────────────────────────────────────────────────────
    ('DLF',         'DLF Limited',                  'Real Estate',   980.00),
    ('GODREJPROP',  'Godrej Properties',            'Real Estate',  2980.00),
    ('OBEROIRLTY',  'Oberoi Realty',                'Real Estate',  1980.00),

    # ── Aviation & Hospitality ────────────────────────────────────────────────
    ('INDIGO',      'InterGlobe Aviation (IndiGo)', 'Aviation',     4800.00),
    ('IRCTC',       'Indian Railway Catering',      'Services',     1020.00),
]


class Command(BaseCommand):
    help = 'Seed stocks and create wallets for all users'

    def handle(self, *args, **kwargs):
        # Seed all stocks — update_or_create
        created_count = 0
        updated_count = 0

        for symbol, name, sector, price in STOCKS:
            _, created = Stock.objects.update_or_create(
                symbol=symbol,
                defaults={
                    'company_name':  name,
                    'sector':        sector,
                    'current_price': Decimal(str(price))
                }
            )
            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'Stocks — {created_count} created, {updated_count} updated ({len(STOCKS)} total)'
        ))

        # Create wallets for all existing users, get_or_create means existing wallets are never touched
        wallet_count = 0
        for user in User.objects.all():
            _, created = Wallet.objects.get_or_create(
                student=user,
                defaults={'balance': Decimal('100000.00')}
            )
            if created:
                wallet_count += 1

        self.stdout.write(self.style.SUCCESS(
            f'Wallets — {wallet_count} new wallets created'
        ))