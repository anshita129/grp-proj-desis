"""
python manage.py seed_learning

Seeds the database with:
  - 8 learning modules (with lessons)
  - 1 quiz per module (10 MCQ questions, 4 choices each)
  - 3 badge definitions
"""
from django.core.management.base import BaseCommand
from learning.models import Module, Lesson, Quiz, Question, Choice, Badge


# ────────────────────────────────────────────────────────────
# Module / Lesson data
# ────────────────────────────────────────────────────────────
MODULES = [
    {
        "title": "Introduction to Stock Markets",
        "difficulty": "Beginner",
        "description": "Learn the basics of stock markets — what stocks are, how exchanges work, and who participates.",
        "lessons": [
            ("What Is a Stock?", "A stock represents partial ownership of a company. When you buy shares you become a shareholder entitled to a proportional claim on earnings and assets."),
            ("How Stock Exchanges Work", "Exchanges like the NYSE and NSE are organized marketplaces where buyers and sellers meet. Orders are matched electronically in fractions of a second."),
            ("Understanding Stock Indices", "An index like Nifty 50 or S&P 500 tracks a basket of stocks to represent overall market performance."),
            ("Market Participants", "Key players include retail investors, institutional investors, market makers, and regulators like SEBI."),
            ("Types of Stocks", "Stocks can be classified as common vs preferred, growth vs value, and large-cap vs mid-cap vs small-cap."),
            ("How Stock Prices Move", "Prices are driven by supply and demand, which in turn reflect earnings, news, sentiment, and macroeconomic factors."),
            ("Reading a Stock Quote", "A stock quote shows the ticker symbol, last traded price, day's high/low, volume, and market capitalisation."),
            ("Summary & Key Takeaways", "Stocks represent ownership, exchanges provide liquidity, indices track the market, and prices move on supply and demand."),
        ],
    },
    {
        "title": "Mutual Funds & Diversification",
        "difficulty": "Beginner",
        "description": "Understand how mutual funds pool money, calculate NAV, and why diversification matters.",
        "lessons": [
            ("What Is a Mutual Fund?", "A mutual fund pools money from many investors and invests in a diversified portfolio managed by a professional fund manager."),
            ("Net Asset Value (NAV)", "NAV = (Total Assets − Liabilities) / Outstanding Units. It is the per-unit price of a mutual fund calculated daily."),
            ("Types of Mutual Funds", "Equity funds, debt funds, hybrid funds, index funds, and sectoral funds each have different risk-return profiles."),
            ("Risk vs Return", "Higher expected returns generally come with higher risk. Understanding your risk tolerance is the first step to choosing the right fund."),
            ("Expense Ratio & Fees", "The expense ratio is the annual fee charged by the fund house. Lower expense ratios mean more of your returns stay with you."),
            ("Diversification Explained", "Diversification spreads investments across assets so that a loss in one holding is offset by gains in others, reducing overall portfolio risk."),
            ("SIP — Systematic Investment Plan", "SIP lets you invest a fixed amount at regular intervals, averaging out the purchase cost over time (rupee-cost averaging)."),
            ("Summary & Key Takeaways", "Mutual funds offer professional management and diversification. SIPs make investing disciplined. Always check the expense ratio."),
        ],
    },
    {
        "title": "Reading Financial Statements",
        "difficulty": "Beginner",
        "description": "Learn to read a Profit & Loss statement, Balance Sheet, and Cash Flow statement.",
        "lessons": [
            ("Why Financial Statements Matter", "Financial statements are the report card of a company. They help investors assess profitability, solvency, and cash generation."),
            ("The Profit & Loss Statement", "The P&L (Income Statement) shows revenue, expenses, and net profit over a period — typically a quarter or year."),
            ("Revenue vs Profit", "Revenue is total sales. Gross profit = Revenue − COGS. Operating profit subtracts opex. Net profit subtracts taxes and interest."),
            ("The Balance Sheet", "The balance sheet shows Assets = Liabilities + Equity at a point in time. It reveals what the company owns and owes."),
            ("Current vs Non-Current Assets", "Current assets (cash, receivables) convert to cash within a year. Non-current assets (property, equipment) are long-term."),
            ("The Cash Flow Statement", "Cash flow is split into Operating, Investing, and Financing activities. Positive operating cash flow is a healthy sign."),
            ("Key Financial Ratios", "P/E ratio, debt-to-equity, ROE, and current ratio are quick ways to compare companies within the same sector."),
            ("Putting It All Together", "Read the P&L for profitability, the balance sheet for financial health, and the cash flow statement for liquidity."),
            ("Common Red Flags", "Rising debt with flat revenue, negative operating cash flow, and frequent one-time charges are warning signs."),
            ("Summary & Key Takeaways", "Master the three statements and key ratios to make informed investment decisions."),
        ],
    },
    {
        "title": "Risk & Risk Management",
        "difficulty": "Beginner",
        "description": "Understand types of investment risk and strategies to manage them.",
        "lessons": [
            ("What Is Risk?", "Risk is the possibility that an investment's actual return will differ from the expected return, including the chance of losing money."),
            ("Types of Risk", "Market risk, credit risk, liquidity risk, inflation risk, and concentration risk each affect portfolios differently."),
            ("Measuring Risk — Volatility & Beta", "Standard deviation measures total volatility. Beta measures sensitivity to market movements. Beta > 1 means more volatile than the market."),
            ("Stop-Loss Orders", "A stop-loss automatically sells a stock when it falls to a set price, limiting your downside on any single position."),
            ("Position Sizing", "Never risk more than a small percentage (e.g., 2%) of your portfolio on a single trade. This preserves capital over many trades."),
            ("Diversification as Risk Management", "Holding assets with low correlation reduces portfolio variance. Mix asset classes, sectors, and geographies."),
            ("Risk-Reward Ratio", "Before entering a trade, calculate the ratio of potential profit to potential loss. A ratio of 2:1 or higher is generally desirable."),
            ("Summary & Key Takeaways", "Identify risks, size positions carefully, use stop-losses, diversify, and always evaluate the risk-reward ratio."),
        ],
    },
    {
        "title": "Technical Analysis Basics",
        "difficulty": "Intermediate",
        "description": "Learn to read price charts, identify patterns, and use key indicators.",
        "lessons": [
            ("What Is Technical Analysis?", "Technical analysis studies past price and volume data to forecast future price movements, based on the idea that history tends to repeat."),
            ("Candlestick Charts", "Each candle shows open, high, low, and close for a period. Green/white = bullish (close > open), red/black = bearish (close < open)."),
            ("Support & Resistance", "Support is a price level where buying pressure prevents further decline. Resistance is where selling pressure prevents further rise."),
            ("Trend Lines & Channels", "Connect swing lows for an uptrend line, swing highs for a downtrend line. A channel forms when both lines run parallel."),
            ("Moving Averages", "SMA and EMA smooth out price data. A 50-day MA crossing above a 200-day MA is called a golden cross — a bullish signal."),
            ("Volume Analysis", "Rising prices on rising volume confirm a trend. Rising prices on falling volume suggest weakening momentum."),
            ("RSI — Relative Strength Index", "RSI ranges 0–100. Above 70 is overbought (potential sell), below 30 is oversold (potential buy)."),
            ("MACD Indicator", "MACD = 12-EMA − 26-EMA. A signal line crossover indicates momentum shifts. Histogram shows the gap between MACD and signal."),
            ("Chart Patterns", "Head & Shoulders, double top/bottom, triangles, and flags are patterns that signal trend reversals or continuations."),
            ("Summary & Key Takeaways", "Use candlesticks, support/resistance, moving averages, volume, RSI, and MACD together — no single indicator is sufficient."),
        ],
    },
    {
        "title": "Fundamental Analysis",
        "difficulty": "Intermediate",
        "description": "Evaluate a company's intrinsic value using financial data and qualitative factors.",
        "lessons": [
            ("What Is Fundamental Analysis?", "FA estimates a stock's intrinsic value by examining financial statements, industry conditions, and management quality."),
            ("Intrinsic Value & Margin of Safety", "Intrinsic value is the true worth of a stock. Buy only when the market price is well below intrinsic value — that gap is your margin of safety."),
            ("Price-to-Earnings (P/E) Ratio", "P/E = Market Price / EPS. A high P/E may mean overvaluation OR high growth expectations. Always compare within the same sector."),
            ("Price-to-Book (P/B) Ratio", "P/B = Market Price / Book Value per Share. P/B < 1 may indicate undervaluation, but check why — it could signal trouble."),
            ("Return on Equity (ROE)", "ROE = Net Income / Shareholder Equity. Consistently high ROE (>15%) indicates efficient use of shareholder capital."),
            ("Economic Moats", "A moat is a durable competitive advantage — brand, network effects, cost leadership, or switching costs — that protects profits."),
            ("Management Quality", "Look at the track record, capital allocation decisions, insider ownership, and corporate governance practices."),
            ("Industry & Competitive Analysis", "Use Porter's Five Forces: rivalry, threat of new entrants, substitutes, buyer power, and supplier power."),
            ("Valuation Models — DCF Basics", "Discounted Cash Flow projects future free cash flows and discounts them to present value. Sensitive to growth and discount rate assumptions."),
            ("Summary & Key Takeaways", "Combine financial ratios, moat analysis, management review, and DCF to arrive at a well-rounded valuation."),
        ],
    },
    {
        "title": "Long-Term Investing Principles",
        "difficulty": "Intermediate",
        "description": "Build wealth over time through compounding, SIPs, and disciplined portfolio construction.",
        "lessons": [
            ("The Power of Compounding", "Compounding earns returns on previous returns. Starting early and staying invested turns small amounts into large wealth over decades."),
            ("CAGR — Compound Annual Growth Rate", "CAGR = (Ending Value / Beginning Value)^(1/n) − 1. It smooths out volatility to show annualised growth."),
            ("SIP vs Lump Sum", "SIP invests regularly and benefits from rupee-cost averaging. Lump sum invests all at once — better if markets are low, worse if at a peak."),
            ("Asset Allocation", "Divide your portfolio among equity, debt, gold, and cash based on your age, goals, and risk tolerance."),
            ("Rebalancing Your Portfolio", "Periodically sell outperformers and buy underperformers to maintain your target allocation — this enforces buy-low-sell-high discipline."),
            ("Tax-Efficient Investing", "Understand LTCG vs STCG tax rates. Hold equity for over one year to benefit from lower long-term capital gains tax."),
            ("Building a Core-Satellite Portfolio", "Core holdings are low-cost index funds for stability. Satellite holdings are individual stocks or thematic funds for alpha."),
            ("Summary & Key Takeaways", "Start early, stay invested, use SIPs, diversify across asset classes, rebalance, and keep taxes in mind."),
        ],
    },
    {
        "title": "Behavioural Finance & Psychology",
        "difficulty": "Advanced",
        "description": "Recognise cognitive biases and emotional traps that lead to poor investment decisions.",
        "lessons": [
            ("Why Psychology Matters in Investing", "Markets are moved by people. Understanding biases helps you avoid systematic errors and make rational decisions."),
            ("Loss Aversion", "Losses hurt roughly twice as much as equivalent gains feel good. This makes investors hold losers too long and sell winners too early."),
            ("FOMO — Fear of Missing Out", "FOMO drives investors to chase rallies and buy at peaks. Recognise it: if the reason you're buying is 'everyone else is', step back."),
            ("Overconfidence Bias", "Overconfident investors trade too often, underestimate risk, and overestimate their ability to pick winners."),
            ("Herd Mentality", "Following the crowd feels safe but often leads to buying high and selling low. Independent analysis beats consensus."),
            ("Anchoring Bias", "Anchoring to a past price ('it was ₹500, now it's ₹300 — it's cheap!') ignores whether the current price reflects true value."),
            ("Emotional Discipline", "Create an investment plan, write down your rules, and follow them mechanically. Journaling trades helps identify emotional patterns."),
            ("Summary & Key Takeaways", "Know your biases, have a written plan, avoid herd behaviour, and review decisions objectively."),
        ],
    },
]


# ────────────────────────────────────────────────────────────
# Quiz questions per module  (10 MCQs each, 4 choices, 1 correct)
# Format: (question_text, [(choice_text, is_correct), ...])
# ────────────────────────────────────────────────────────────
QUIZ_DATA = {
    "Introduction to Stock Markets": [
        ("What does owning a stock represent?", [("A loan to the company", False), ("Partial ownership of the company", True), ("A fixed-income security", False), ("A government bond", False)]),
        ("Which organisation regulates stock markets in India?", [("RBI", False), ("SEBI", True), ("IRDA", False), ("NABARD", False)]),
        ("What is a stock index?", [("A list of all listed companies", False), ("A basket of stocks representing market performance", True), ("The price of the most expensive stock", False), ("A type of bond", False)]),
        ("What determines a stock's price in the short term?", [("Only the company's profits", False), ("Government regulations", False), ("Supply and demand", True), ("The face value of the stock", False)]),
        ("Which of these is a major Indian stock exchange?", [("NASDAQ", False), ("LSE", False), ("NSE", True), ("HKEX", False)]),
        ("A retail investor is:", [("A bank buying shares", False), ("An individual investing their own money", True), ("A fund manager", False), ("A stock exchange employee", False)]),
        ("Market capitalisation equals:", [("Revenue × P/E ratio", False), ("Share price × number of outstanding shares", True), ("Total assets − total liabilities", False), ("Annual dividend × share price", False)]),
        ("Which type of stock generally pays regular dividends?", [("Growth stock", False), ("Penny stock", False), ("Preferred stock", True), ("IPO stock", False)]),
        ("A 'bull market' refers to:", [("Falling prices", False), ("Rising prices", True), ("Stable prices", False), ("High-volatility sideways market", False)]),
        ("Face value of a stock is:", [("Its market price", False), ("Its intrinsic value", False), ("The nominal value assigned when issued", True), ("The average of high and low price", False)]),
    ],
    "Mutual Funds & Diversification": [
        ("NAV stands for:", [("National Asset Value", False), ("Net Asset Value", True), ("Net Annual Volume", False), ("Nominal Assessed Value", False)]),
        ("Which fund type invests primarily in government bonds?", [("Equity fund", False), ("Debt fund", True), ("Sectoral fund", False), ("Index fund", False)]),
        ("SIP stands for:", [("Stock Investment Plan", False), ("Systematic Investment Plan", True), ("Savings Interest Programme", False), ("Standard Index Portfolio", False)]),
        ("Expense ratio is:", [("The return generated by a fund", False), ("The annual fee charged by the fund", True), ("The tax on mutual fund gains", False), ("The minimum investment amount", False)]),
        ("Diversification helps to:", [("Guarantee profits", False), ("Eliminate all risk", False), ("Reduce overall portfolio risk", True), ("Increase expense ratio", False)]),
        ("An index fund aims to:", [("Beat the market", False), ("Replicate a market index", True), ("Invest only in bonds", False), ("Short-sell stocks", False)]),
        ("Rupee-cost averaging means:", [("Buying at the lowest price always", False), ("Investing equal amounts at regular intervals", True), ("Timing the market precisely", False), ("Investing only when NAV falls", False)]),
        ("Which is the riskiest fund type?", [("Liquid fund", False), ("Debt fund", False), ("Small-cap equity fund", True), ("Overnight fund", False)]),
        ("A hybrid fund invests in:", [("Only equities", False), ("Only debt", False), ("Both equity and debt", True), ("Only gold", False)]),
        ("Exit load is:", [("The fee for buying a fund", False), ("A penalty for early redemption", True), ("The annual management fee", False), ("Tax on capital gains", False)]),
    ],
    "Reading Financial Statements": [
        ("The P&L statement shows:", [("Assets and liabilities", False), ("Revenue and expenses over a period", True), ("Cash inflows and outflows", False), ("Shareholder equity breakdown", False)]),
        ("Gross profit equals:", [("Revenue − Operating Expenses", False), ("Revenue − Cost of Goods Sold", True), ("Net profit + Tax", False), ("Total assets − Total liabilities", False)]),
        ("The balance sheet equation is:", [("Revenue = Expenses + Profit", False), ("Assets = Liabilities + Equity", True), ("Cash In = Cash Out", False), ("Profit = Revenue − Tax", False)]),
        ("Current assets are:", [("Assets that last more than a year", False), ("Assets convertible to cash within a year", True), ("Only cash in hand", False), ("Intangible assets", False)]),
        ("Operating cash flow being negative means:", [("The company is profitable", False), ("Core business isn't generating cash", True), ("The company paid a dividend", False), ("Investments are growing", False)]),
        ("P/E ratio measures:", [("Profit to equity", False), ("Price relative to earnings per share", True), ("Assets to liabilities", False), ("Revenue growth rate", False)]),
        ("Debt-to-equity ratio above 2 generally suggests:", [("Low financial risk", False), ("High leverage", True), ("The company is debt-free", False), ("Strong cash reserves", False)]),
        ("ROE stands for:", [("Return on Expenditure", False), ("Return on Equity", True), ("Rate of Exchange", False), ("Revenue over Expenses", False)]),
        ("Which statement shows dividends paid?", [("P&L statement", False), ("Balance sheet", False), ("Cash flow from financing activities", True), ("Notes to accounts only", False)]),
        ("A red flag in financial statements is:", [("Growing revenue with growing profits", False), ("Consistent positive operating cash flow", False), ("Rising debt with flat revenue", True), ("Decreasing expense ratio", False)]),
    ],
    "Risk & Risk Management": [
        ("Market risk is also called:", [("Credit risk", False), ("Systematic risk", True), ("Liquidity risk", False), ("Concentration risk", False)]),
        ("Beta greater than 1 means the stock is:", [("Less volatile than the market", False), ("More volatile than the market", True), ("Uncorrelated with the market", False), ("A bond", False)]),
        ("A stop-loss order:", [("Guarantees a profit", False), ("Limits potential losses by auto-selling", True), ("Buys more shares when price falls", False), ("Is only for institutional investors", False)]),
        ("Position sizing refers to:", [("The total value of your portfolio", False), ("How much to invest in a single trade", True), ("The number of stocks in an index", False), ("The size of the stock exchange", False)]),
        ("Diversification reduces:", [("Systematic risk", False), ("Unsystematic risk", True), ("All risk completely", False), ("Transaction costs", False)]),
        ("The 2% rule in trading suggests:", [("Invest 2% in bonds", False), ("Never risk more than 2% of capital on one trade", True), ("Keep 2% cash always", False), ("Limit trades to 2 per day", False)]),
        ("Risk-reward ratio of 3:1 means:", [("Risk ₹3 to make ₹1", False), ("Risk ₹1 to potentially make ₹3", True), ("The stock moves 3% daily", False), ("The expense ratio is 3%", False)]),
        ("Inflation risk is the risk that:", [("Stock prices crash", False), ("Returns don't keep up with rising prices", True), ("Interest rates fall", False), ("The company goes bankrupt", False)]),
        ("Liquidity risk means:", [("The investment is too profitable", False), ("You may not be able to sell quickly at fair price", True), ("The company has too much cash", False), ("Markets are always open", False)]),
        ("Which is NOT a risk management technique?", [("Diversification", False), ("Stop-loss orders", False), ("Position sizing", False), ("Ignoring market news", True)]),
    ],
    "Technical Analysis Basics": [
        ("Technical analysis primarily studies:", [("Company financials", False), ("Past price and volume data", True), ("Management quality", False), ("GDP growth", False)]),
        ("A green/white candlestick means:", [("Close < Open (bearish)", False), ("Close > Open (bullish)", True), ("No trading occurred", False), ("Volume was zero", False)]),
        ("Support level is where:", [("Selling pressure is strong", False), ("Buying pressure prevents further decline", True), ("The stock always reverses", False), ("Volume drops to zero", False)]),
        ("A golden cross occurs when:", [("50-day MA crosses above 200-day MA", True), ("Price hits an all-time high", False), ("RSI crosses 50", False), ("MACD turns negative", False)]),
        ("RSI above 70 suggests a stock is:", [("Oversold", False), ("Overbought", True), ("Fairly valued", False), ("Delisted", False)]),
        ("Rising price with falling volume suggests:", [("Strong uptrend", False), ("Weakening momentum", True), ("Panic selling", False), ("Institutional buying", False)]),
        ("MACD stands for:", [("Moving Average Convergence Divergence", True), ("Market Average Cost Differential", False), ("Median Annual Capital Distribution", False), ("Multiple Asset Class Diversification", False)]),
        ("A head-and-shoulders pattern signals:", [("Trend continuation", False), ("Trend reversal", True), ("Sideways movement forever", False), ("Increased dividends", False)]),
        ("A resistance level is:", [("A price floor", False), ("A price ceiling where selling pressure increases", True), ("The lowest price ever", False), ("The IPO price", False)]),
        ("Which indicator ranges from 0 to 100?", [("MACD", False), ("Moving Average", False), ("RSI", True), ("Bollinger Bands", False)]),
    ],
    "Fundamental Analysis": [
        ("Fundamental analysis evaluates:", [("Chart patterns", False), ("A company's intrinsic value using financial data", True), ("Short-term price momentum", False), ("Candlestick formations", False)]),
        ("Margin of safety means:", [("Extra insurance on your portfolio", False), ("Buying below estimated intrinsic value", True), ("Keeping 50% cash", False), ("Only investing in AAA bonds", False)]),
        ("A P/E ratio of 30 vs industry average of 15 suggests:", [("Stock may be undervalued", False), ("Stock may be overvalued or high-growth", True), ("The company is in debt", False), ("Earnings are negative", False)]),
        ("ROE measures:", [("Revenue efficiency", False), ("How well shareholder equity generates profit", True), ("Debt coverage", False), ("Market share", False)]),
        ("An economic moat is:", [("A financial ratio", False), ("A durable competitive advantage", True), ("A type of stock order", False), ("A government subsidy", False)]),
        ("Porter's Five Forces include:", [("Only buyer and supplier power", False), ("Rivalry, new entrants, substitutes, buyer power, supplier power", True), ("Only industry growth rate", False), ("P/E, P/B, ROE, ROCE, EPS", False)]),
        ("P/B ratio less than 1 may indicate:", [("Guaranteed profit", False), ("Possible undervaluation", True), ("The company has no assets", False), ("High growth ahead", False)]),
        ("DCF stands for:", [("Debt Coverage Factor", False), ("Discounted Cash Flow", True), ("Direct Cost Framework", False), ("Dividend Compound Frequency", False)]),
        ("Management quality can be assessed by:", [("Stock price alone", False), ("Track record, capital allocation, governance", True), ("Number of employees", False), ("Office location", False)]),
        ("Which is a qualitative factor in FA?", [("P/E ratio", False), ("Brand strength and moat", True), ("Debt-to-equity ratio", False), ("Earnings per share", False)]),
    ],
    "Long-Term Investing Principles": [
        ("Compounding means:", [("Earning returns on previous returns", True), ("Doubling your investment every year", False), ("Only investing in fixed deposits", False), ("Eliminating all risk", False)]),
        ("CAGR stands for:", [("Current Annual Gross Return", False), ("Compound Annual Growth Rate", True), ("Capital Adjusted Gain Ratio", False), ("Compounded Average Guaranteed Return", False)]),
        ("SIP benefits from:", [("Market timing", False), ("Rupee-cost averaging", True), ("Guaranteed returns", False), ("Zero risk", False)]),
        ("Asset allocation means:", [("Buying only stocks", False), ("Dividing investments among asset classes", True), ("Keeping all money in savings", False), ("Investing only internationally", False)]),
        ("Rebalancing enforces:", [("Buy-high-sell-low", False), ("Buy-low-sell-high discipline", True), ("Ignoring market changes", False), ("Only buying more stocks", False)]),
        ("LTCG tax on equity held over 1 year in India is:", [("Exempt up to a limit, then taxed at a lower rate", True), ("Taxed at 30%", False), ("Not applicable", False), ("Same as salary income tax", False)]),
        ("A core-satellite portfolio uses:", [("Only active funds", False), ("Index funds as core, active picks as satellite", True), ("Only gold and bonds", False), ("Leverage for all positions", False)]),
        ("Starting to invest early is important because:", [("You can time the market better", False), ("Compounding has more time to work", True), ("Taxes are lower for young investors", False), ("Markets are less volatile when you're young", False)]),
        ("Lump sum investing is better when:", [("Markets are at a peak", False), ("Markets are at a low point", True), ("Interest rates are high", False), ("You have no emergency fund", False)]),
        ("Which is NOT a long-term investing principle?", [("Stay invested through volatility", False), ("Day-trade for quick profits", True), ("Diversify across asset classes", False), ("Rebalance periodically", False)]),
    ],
    "Behavioural Finance & Psychology": [
        ("Loss aversion means investors:", [("Love taking losses", False), ("Feel losses more intensely than equivalent gains", True), ("Never sell losing stocks", False), ("Always buy at the bottom", False)]),
        ("FOMO in investing leads to:", [("Careful analysis", False), ("Chasing rallies and buying at peaks", True), ("Selling at the bottom", False), ("Diversification", False)]),
        ("Overconfidence bias causes investors to:", [("Trade too infrequently", False), ("Trade too often and underestimate risk", True), ("Always seek professional advice", False), ("Avoid all risk", False)]),
        ("Herd mentality means:", [("Independent analysis", False), ("Following what everyone else is doing", True), ("Contrarian investing", False), ("Only listening to experts", False)]),
        ("Anchoring bias is:", [("Setting a stop-loss at purchase price", False), ("Fixating on a past price as reference", True), ("Using moving averages", False), ("Buying only blue-chip stocks", False)]),
        ("Which helps counter emotional trading?", [("Checking prices every minute", False), ("Having a written investment plan", True), ("Following social media tips", False), ("Doubling down on losing positions", False)]),
        ("Recency bias makes investors:", [("Overweight recent events", True), ("Focus on long-term trends", False), ("Ignore all news", False), ("Only buy index funds", False)]),
        ("Confirmation bias is:", [("Seeking information that confirms existing beliefs", True), ("Objectively evaluating all data", False), ("Trusting only financial statements", False), ("Ignoring past performance", False)]),
        ("The disposition effect causes investors to:", [("Sell winners too early and hold losers too long", True), ("Hold winners and sell losers", False), ("Never sell any stock", False), ("Only sell at a profit", False)]),
        ("Best way to manage trading psychology?", [("Trade on gut feeling", False), ("Increase leverage", False), ("Journal trades and review decisions", True), ("Follow the crowd", False)]),
    ],
}


# ────────────────────────────────────────────────────────────
# Badges
# ────────────────────────────────────────────────────────────
BADGES = [
    {"name": "First Quiz Passed", "description": "Awarded when you pass your first quiz.", "icon_name": "star"},
    {"name": "Perfect Score", "description": "Awarded when you score 10/10 on any quiz.", "icon_name": "trophy"},
    {"name": "All Modules Complete", "description": "Awarded when you pass all 8 module quizzes.", "icon_name": "crown"},
]


class Command(BaseCommand):
    help = "Seed 8 learning modules with lessons, quizzes (10 MCQs each), and 3 badges."

    def handle(self, *args, **options):
        # ── Badges ──
        for b in BADGES:
            Badge.objects.update_or_create(name=b["name"], defaults=b)
        self.stdout.write(self.style.SUCCESS(f"✔ {len(BADGES)} badges seeded"))

        # ── Modules, Lessons, Quizzes ──
        for idx, mod_data in enumerate(MODULES, start=1):
            module, _ = Module.objects.update_or_create(
                slug=mod_data["title"].lower().replace(" ", "-").replace("&", "and"),
                defaults={
                    "title": mod_data["title"],
                    "description": mod_data["description"],
                    "difficulty": mod_data["difficulty"],
                    "order": idx,
                },
            )

            # Lessons
            for lesson_order, (l_title, l_content) in enumerate(mod_data["lessons"], start=1):
                Lesson.objects.update_or_create(
                    module=module,
                    order=lesson_order,
                    defaults={"title": l_title, "content": l_content},
                )

            # Quiz
            quiz_questions = QUIZ_DATA.get(mod_data["title"], [])
            if quiz_questions:
                quiz, _ = Quiz.objects.update_or_create(
                    module=module,
                    defaults={"title": f"Quiz: {mod_data['title']}", "pass_mark": 7},
                )
                for q_order, (q_text, choices) in enumerate(quiz_questions, start=1):
                    question, _ = Question.objects.update_or_create(
                        quiz=quiz,
                        order=q_order,
                        defaults={"text": q_text},
                    )
                    for c_text, c_correct in choices:
                        Choice.objects.update_or_create(
                            question=question,
                            text=c_text,
                            defaults={"is_correct": c_correct},
                        )

            self.stdout.write(f"  Module {idx}: {mod_data['title']} — {len(mod_data['lessons'])} lessons, {len(quiz_questions)} questions")

        self.stdout.write(self.style.SUCCESS("✔ Seed complete!"))
