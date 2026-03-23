"""
python manage.py enrich_lessons

Updates every lesson with rich multi-paragraph content and a relevant image URL.
Safe to re-run (uses update_or_create logic on title+module).
"""
from django.core.management.base import BaseCommand
from learning.models import Module, Lesson

IMG = "https://images.unsplash.com/photo-"
W = "?w=1200&q=80&auto=format&fit=crop"

# (module_title, lesson_title) -> (image_url, rich_content)
LESSON_ENRICHMENT = {

    # ── Module 1: Introduction to Stock Markets ──────────────────
    ("Introduction to Stock Markets", "What Is a Stock?"): (
        IMG + "1611974789855-9c2a0a7236a3" + W,
        """A stock — also called a share or equity — represents a unit of ownership in a company. When a business wants to raise capital, it can divide itself into millions of small ownership stakes and sell them to the public through a process called an Initial Public Offering (IPO). Each person who buys one of those stakes becomes a shareholder.

As a shareholder you have a proportional claim on the company's earnings and assets. If the company profits, those profits may be returned to you as dividends, or they may be reinvested to grow the business — increasing the stock's value over time. If the company is liquidated, shareholders receive what remains after creditors and bondholders are paid.

Stocks are bought and sold on stock exchanges every trading day. The price at which a stock trades reflects the collective opinion of all market participants about that company's current and future worth. Understanding what a stock actually is forms the bedrock of every investing decision you will ever make — so it is worth getting this concept crystal clear before moving on."""
    ),

    ("Introduction to Stock Markets", "How Stock Exchanges Work"): (
        IMG + "1590283603385-17ffb3a7f29f" + W,
        """A stock exchange is an organised, regulated marketplace where buyers and sellers come together to trade shares. Major examples include the New York Stock Exchange (NYSE), NASDAQ in the United States, the National Stock Exchange (NSE) and the Bombay Stock Exchange (BSE) in India. These venues provide price transparency, liquidity, and a legal framework that protects all participants.

Modern exchanges are almost entirely electronic. When you place a buy order, a matching engine searches for a seller willing to accept your price. If a match is found, the trade executes in microseconds. Prices move continuously throughout the trading session as new orders arrive, reflecting every piece of new information traders act upon.

Behind the scenes, a clearing house guarantees settlement — ensuring you receive the shares and the seller receives the cash, usually within one to two business days (called T+1 or T+2 settlement). Exchanges also enforce listing standards: companies must meet minimum requirements for revenue, profitability, and governance to be listed, giving investors a baseline level of confidence."""
    ),

    ("Introduction to Stock Markets", "Understanding Stock Indices"): (
        IMG + "1642543492481-44e81e3914a7" + W,
        """A stock index is a statistical measure that tracks the performance of a selected group of stocks. The Sensex tracks the 30 largest companies on the BSE; the Nifty 50 tracks 50 large-caps on the NSE; the S&P 500 tracks 500 major US companies. Rather than watching thousands of stocks individually, investors watch indices to gauge the health of the overall market or a specific segment of it.

Most major indices are market-capitalisation weighted, meaning larger companies have a bigger influence on the index's movement. If a giant company like Reliance or Apple rises sharply, the index rises more than if a smaller company makes the same move. Price-weighted indices like the Dow Jones Industrial Average instead give heavier weight to higher-priced stocks.

Indices serve as benchmarks. When a mutual fund manager says "we beat the market by 3%", they mean their portfolio grew 3% more than the relevant index. Index funds and ETFs replicate indices passively, giving ordinary investors broad market exposure at very low cost — an insight that has transformed global investing over the past three decades."""
    ),

    ("Introduction to Stock Markets", "Market Participants"): (
        IMG + "1454165804606-c3d57bc86b40" + W,
        """The stock market is a vast ecosystem with many different types of participants, each playing a distinct role. Retail investors are individuals like you — they invest their own savings, typically in smaller amounts. Institutional investors — mutual funds, pension funds, insurance companies, and hedge funds — move enormous sums and collectively drive a large portion of daily trading volume.

Market makers are firms that continuously quote buy and sell prices, ensuring there is always a counterparty available for a trade. They profit from the bid-ask spread and play a vital role in keeping markets liquid. Foreign Institutional Investors (FIIs) or Foreign Portfolio Investors (FPIs) bring or withdraw capital from a country based on global risk appetite, often causing large short-term swings.

Regulators oversee it all. In India, SEBI (Securities and Exchange Board of India) sets rules, prosecutes insider trading, and ensures fair disclosure. Exchanges self-regulate within SEBI's framework. Understanding who the other players are — their motivations, constraints, and time horizons — helps you anticipate market behaviour rather than being surprised by it."""
    ),

    ("Introduction to Stock Markets", "Types of Stocks"): (
        IMG + "1579621970588-a35d0e7ab9b6" + W,
        """Not all stocks are created equal. Common stock is the standard form of equity — it carries voting rights and a claim on residual profits. Preferred stock pays a fixed dividend before common shareholders receive anything and has priority during liquidation, but usually has no voting rights. Most retail investors hold common stock.

Stocks are also categorised by company size. Large-cap stocks (market cap above ₹20,000 crore in India) are established, relatively stable businesses. Mid-cap stocks offer growth potential with moderate risk. Small-cap stocks can deliver explosive returns but come with higher volatility and lower liquidity. Within these, growth stocks are expected to increase earnings rapidly — often trading at high valuations — while value stocks trade below what the investor believes is their true worth.

Sector classification matters too. Banking stocks behave differently from technology stocks, which behave differently from FMCG stocks. Cyclical stocks (auto, steel, real estate) track the economic cycle closely, rising in booms and falling in recessions. Defensive stocks (pharma, utilities, consumer staples) hold up relatively well in downturns because demand for their products remains stable regardless of economic conditions."""
    ),

    ("Introduction to Stock Markets", "How Stock Prices Move"): (
        IMG + "1551288049-bebda4e38f71" + W,
        """At the most fundamental level, stock prices move because of supply and demand. When more people want to buy a stock than sell it, the price rises. When sellers outnumber buyers, the price falls. But what drives those buying and selling decisions? Almost everything — earnings reports, economic data, interest rate changes, geopolitical events, management changes, product launches, and even social media sentiment.

In the short run, prices are heavily influenced by market psychology — fear and greed cause dramatic swings that have little to do with a company's underlying value. This is why stocks can lose 30% of their value in a month despite the business being perfectly healthy, or rise 50% even as the company loses money, simply because investors expect future profits.

Over the long run, however, stock prices tend to track earnings growth. A company that consistently grows its revenue and profits will see its stock price rise over years and decades. This is the key insight that underpins long-term investing: ignore the daily noise, focus on the underlying business, and let time do the heavy lifting."""
    ),

    ("Introduction to Stock Markets", "Reading a Stock Quote"): (
        IMG + "1526304640581-d334cdbbf45e" + W,
        """A stock quote is a snapshot of a stock's current and recent trading information. The ticker symbol (e.g., RELIANCE, TCS, INFY) uniquely identifies the company on the exchange. The last traded price (LTP) is the most recent price at which the stock changed hands. The day's high and low show the price range during the current trading session.

Volume tells you how many shares have been traded today — high volume on a significant price move confirms the move is meaningful; low volume suggests it may not last. Market capitalisation (market cap) is the total value of all outstanding shares: it equals share price × number of shares. A ₹100 share with 10 crore shares outstanding has a ₹1,000 crore market cap.

Other key fields you will see: the 52-week high and low (useful for context), the P/E ratio (we'll cover this in detail later), the dividend yield (annual dividend ÷ current price, expressed as a percentage), and the face value (the nominal value assigned at the time the company was incorporated — often ₹1, ₹2, or ₹10 — which has little relationship to the market price)."""
    ),

    ("Introduction to Stock Markets", "Summary & Key Takeaways"): (
        IMG + "1504711434969-e33886168f5c" + W,
        """You have now covered the essential building blocks of stock market knowledge. A stock is a unit of ownership; exchanges are the regulated venues where stocks trade; indices track groups of stocks as market benchmarks; and prices are driven by supply, demand, and the collective expectations of thousands of market participants.

You have learned who participates in markets — retail investors, institutions, market makers, and regulators — and why each behaves differently. You know that stocks come in many varieties: common vs preferred, large vs small cap, growth vs value, cyclical vs defensive. And you understand that short-term price movement is driven by psychology, while long-term price movement tracks business performance.

These fundamentals will be your compass for every module that follows. Before moving on, make sure you can answer: What does owning one share of a company actually mean? Who sets the price? What does a stock index measure? If you can answer these clearly, you are ready to go deeper."""
    ),

    # ── Module 2: Mutual Funds & Diversification ──────────────────
    ("Mutual Funds & Diversification", "What Is a Mutual Fund?"): (
        IMG + "1559526323-cb2f2fe2591b" + W,
        """A mutual fund is an investment vehicle that pools money from many individual investors and uses that collective capital to buy a diversified portfolio of securities — stocks, bonds, or a mix of both. A professional fund manager makes the investment decisions on behalf of all investors, selecting securities according to the fund's stated objective (e.g., "generate long-term capital appreciation from large-cap equities").

Each investor owns units of the fund proportional to their investment. If you invest ₹10,000 in a fund that has a total corpus of ₹100 crore, you own 0.001% of everything in the portfolio. As the value of the underlying securities rises or falls, the value of your units does too. This is why mutual funds are called "pass-through" vehicles — the returns pass through to investors minus the management fee.

Mutual funds democratise investing. Before they existed, building a diversified portfolio of 50+ stocks required significant capital and expertise. Today, an investor with ₹500 per month can own a tiny slice of India's 50 largest companies through a Nifty 50 index fund. This accessibility, combined with professional management, has made mutual funds the most popular investment vehicle for first-time investors worldwide."""
    ),

    ("Mutual Funds & Diversification", "Net Asset Value (NAV)"): (
        IMG + "1526304640581-d334cdbbf45e" + W,
        """NAV stands for Net Asset Value and is the per-unit price of a mutual fund. It is calculated at the end of every trading day using a simple formula: NAV = (Total Market Value of Securities − Liabilities) ÷ Number of Outstanding Units. If a fund holds stocks worth ₹100 crore, has liabilities of ₹2 crore, and has issued 50 lakh units, its NAV is ₹196 per unit.

When you buy a mutual fund, you purchase units at the current NAV (plus any applicable entry load, though most Indian funds have removed entry loads). When you redeem, you receive the NAV at the end of the processing day (or the next business day for some funds). Unlike stocks, you cannot buy or sell mutual fund units at real-time prices throughout the day — NAV is fixed once per day after market close.

A higher NAV does not mean a fund is expensive or a lower NAV that it is cheap. NAV simply reflects accumulated growth. A fund with NAV ₹500 that has grown from ₹10 over 15 years has delivered extraordinary returns. A newer fund with NAV ₹15 is not "cheaper" — the percentage return on future growth is what matters, not the absolute price of a unit."""
    ),

    ("Mutual Funds & Diversification", "Types of Mutual Funds"): (
        IMG + "1614728894747-a83421e2b9c9" + W,
        """Mutual funds are classified primarily by the asset class they invest in. Equity funds invest predominantly in stocks — they carry higher risk but historically deliver higher long-term returns. Within equity, you have large-cap, mid-cap, small-cap, multi-cap, ELSS (tax-saving), thematic, and sectoral funds, each with a different risk-return profile. Debt funds invest in bonds, government securities, and money market instruments — lower risk, more predictable returns.

Hybrid funds blend equity and debt in varying proportions. Aggressive hybrid funds might keep 65–80% in equities, while conservative hybrid funds might hold mainly debt. Balanced advantage funds dynamically shift allocation based on market valuations. Index funds and ETFs (Exchange Traded Funds) passively replicate an index like the Nifty 50, keeping costs very low. They have no fund manager actively choosing stocks.

SEBI has standardised mutual fund categories in India to make comparisons easier. Before investing, read the scheme information document (SID) to understand exactly what a fund can and cannot invest in, its benchmark, and its historical performance. Past performance is not a guarantee of future results, but comparing a fund's returns against its benchmark and category peers over 3, 5, and 10 years gives you a meaningful picture of manager skill."""
    ),

    ("Mutual Funds & Diversification", "Risk vs Return"): (
        IMG + "1611974789855-9c2a0a7236a3" + W,
        """Every investment involves a trade-off between risk and return. In finance, risk refers to the uncertainty of outcomes — the possibility that an investment's actual return will differ from what you expected. Higher potential returns almost always come with higher risk. This relationship is one of the most fundamental truths in all of investing.

Equity mutual funds can deliver 12–15% annual returns over long periods, but they can also fall 30–50% in a bad year. Debt funds targeting 6–8% annual returns are much more stable but will never produce the wealth-compounding power of equities. Liquid funds targeting 4–6% are the most stable, essentially functioning as a safe parking place for short-term cash.

Your risk tolerance — the amount of uncertainty you can accept without losing sleep or making panic decisions — should guide your fund selection. Risk tolerance has two dimensions: financial (can your household survive a 30% portfolio drop without needing to sell investments?) and psychological (will you stay invested through a crash, or will fear override your plan?). Aligning your investments with your genuine risk tolerance, rather than your aspirational risk tolerance, is one of the most important decisions you will make as an investor."""
    ),

    ("Mutual Funds & Diversification", "Expense Ratio & Fees"): (
        IMG + "1543286386-713bdd548da4" + W,
        """The expense ratio is the annual fee a mutual fund charges for managing your money, expressed as a percentage of your average daily net assets. If a fund has an expense ratio of 1.5% and you have ₹1,00,000 invested, you pay ₹1,500 per year in fees — whether the fund goes up, down, or sideways. This fee is deducted from the fund's NAV daily, so it is invisible in your account but very real in its impact.

Over long periods, expense ratios have an enormous compounding effect. Consider ₹10 lakh invested for 30 years at 12% gross return: with a 0.1% expense ratio (typical index fund) you end with approximately ₹1.74 crore; with a 1.5% expense ratio (typical active fund) you end with approximately ₹1.33 crore. The fee difference alone costs you ₹41 lakh. This is why index fund advocates argue so strongly for low costs.

In India, direct plans of mutual funds have lower expense ratios than regular plans, because regular plans pay a commission to the distributor who sold you the fund. If you invest directly with the AMC (Asset Management Company) or through a direct-plan platform, you can save 0.5–1% per year in distributor commissions. Over a 20-year investment horizon, this can amount to 15–20% more wealth."""
    ),

    ("Mutual Funds & Diversification", "Diversification Explained"): (
        IMG + "1466354424719-343280fe118b" + W,
        """Diversification is the practice of spreading investments across different assets, sectors, and geographies so that a loss in any single holding has a limited impact on your overall portfolio. The mathematical intuition is correlation: if two assets tend to move in opposite directions (negative correlation), holding both reduces the volatility of the combined portfolio even if the individual assets remain risky.

In practice, diversification means not owning just one stock, one sector, or one asset class. An investor who put everything into IT stocks in the early 2000s suffered catastrophically when the dot-com bubble burst. An investor who held IT stocks alongside banking, FMCG, and pharma stocks — plus some gold and bonds — experienced a much smoother ride. Diversification does not eliminate risk; it eliminates the risk that is specific to a single company or sector (called unsystematic or idiosyncratic risk).

Systematic risk — the risk that affects all assets simultaneously, like a global recession or pandemic — cannot be diversified away. This residual risk is what investors are compensated for by the market's long-term risk premium. Mutual funds are inherently diversified products: a single Nifty 50 index fund unit gives you exposure to 50 carefully selected companies across multiple sectors, providing an easy, low-cost path to diversification for any investor."""
    ),

    ("Mutual Funds & Diversification", "SIP — Systematic Investment Plan"): (
        IMG + "1535320903710-d993d3d77d29" + W,
        """A Systematic Investment Plan (SIP) is an investment method where you commit to investing a fixed amount into a mutual fund at regular intervals — typically monthly. When the NAV is high, your fixed amount buys fewer units; when the NAV is low, it buys more units. Over time, this averages out your purchase price — a concept called rupee-cost averaging (or dollar-cost averaging in international parlance).

SIPs are powerful for several reasons beyond cost-averaging. They make investing automatic and habitual, removing the temptation to time the market. They work with almost any budget — many funds accept SIPs as low as ₹100 or ₹500 per month. And they allow ordinary salaried investors to participate in equity markets without needing a large lump sum upfront.

Consider the mathematics: ₹5,000 per month invested for 20 years at 12% per annum grows to approximately ₹49.9 lakh. The same amount invested for 30 years at the same return grows to ₹1.76 crore. The extra 10 years more than triples your outcome — demonstrating why starting your SIP early, even with small amounts, is so much more powerful than waiting to invest larger amounts later."""
    ),

    ("Mutual Funds & Diversification", "Summary & Key Takeaways"): (
        IMG + "1504711434969-e33886168f5c" + W,
        """Mutual funds pool money from many investors to build diversified portfolios managed by professionals. NAV is the daily per-unit price, calculated by dividing the fund's net assets by outstanding units. Funds come in many types — equity, debt, hybrid, and index — each suited to different risk appetites and investment horizons.

Expense ratios are the silent assassin of long-term wealth. Choosing low-cost direct plans and index funds rather than high-cost active regular plans can add millions of rupees to your retirement corpus over time. Diversification — the core promise of a mutual fund — reduces unsystematic risk, though systematic market risk always remains.

SIPs are the most practical way for salaried investors to build wealth: fixed monthly contributions leveraging rupee-cost averaging, compound growth, and the discipline of automated investing. Start early, stay consistent, keep costs low, and leave your investments undisturbed through market cycles. These four habits alone, applied faithfully over 20–30 years, can transform a modest income into significant wealth."""
    ),

    # ── Module 3: Reading Financial Statements ────────────────────
    ("Reading Financial Statements", "Why Financial Statements Matter"): (
        IMG + "1568515387631-8b650bbcdb90" + W,
        """Financial statements are the official report card of a public company. Every listed company is required by law to publish them quarterly and annually. They contain a wealth of data — revenue, costs, profits, assets, debts, and cash flows — that form the factual foundation for any investment decision. Without reading them, you are essentially investing blind.

There are three core financial statements: the Profit & Loss (Income) Statement, the Balance Sheet, and the Cash Flow Statement. Together, they tell you whether the company is profitable (P&L), whether it is financially healthy (Balance Sheet), and whether it is actually generating real cash from its operations (Cash Flow). No single statement tells the full story; you need all three.

Fortunately, you do not need an accounting degree to understand the basics. Once you can read the three statements and calculate a handful of key ratios, you will be better equipped than the majority of retail investors who rely entirely on headlines, tips, and stock screeners. This module will walk you through each statement step by step."""
    ),

    ("Reading Financial Statements", "The Profit & Loss Statement"): (
        IMG + "1568515387631-8b650bbcdb90" + W,
        """The Profit & Loss statement (P&L), also called the Income Statement, summarises a company's revenues and expenses over a defined period — typically a financial quarter (April–June, July–September, etc.) or a full financial year. The final line — Net Profit or Net Loss — tells you whether the company made or lost money during that period.

The P&L is structured in tiers. Starting from the top: Revenue (all money earned from selling products or services), then deducting Cost of Goods Sold (COGS) gives Gross Profit. Deducting operating expenses (salaries, rent, marketing, R&D) gives Operating Profit (also called EBIT: Earnings Before Interest and Tax). Deducting interest expense and tax gives the final Net Profit.

Each tier tells you something specific. A company with high gross profit but low operating profit is spending too much on overheads. A company with high operating profit but low net profit may be over-leveraged (lots of interest payments). Tracking these lines over multiple quarters — not just one — reveals the trend: is the business becoming more or less efficient, more or less profitable?"""
    ),

    ("Reading Financial Statements", "Revenue vs Profit"): (
        IMG + "1611974789855-9c2a0a7236a3" + W,
        """Revenue and profit are often confused, but they are critically different. Revenue (also called topline or turnover) is the total amount of money a company receives from its customers. Profit is what remains after all costs — the bottomline. A company can have enormous revenue and still lose money if its costs are higher than its income. Conversely, a company can have modest revenue but high profit if it operates with low costs and high margins.

Gross profit margin = (Gross Profit ÷ Revenue) × 100. A 60% gross margin means the company earns ₹60 in raw profit for every ₹100 of sales before accounting for operating costs. Net profit margin = (Net Profit ÷ Revenue) × 100. A 15% net margin means ₹15 reaches the bottom line for every ₹100 earned. These ratios are more useful than absolute numbers because they allow comparison across companies of different sizes and across time.

Watch out for revenue growth without corresponding profit growth — it can signal a business that is discounting aggressively to win customers but cannot sustainably monetise them. Also watch for one-time items (asset sales, tax benefits, write-offs) that inflate or deflate profit in a single period. Adjusting for these exceptional items gives you a cleaner view of the company's underlying earning power."""
    ),

    ("Reading Financial Statements", "The Balance Sheet"): (
        IMG + "1642543492481-44e81e3914a7" + W,
        """The balance sheet is a financial photograph of a company at a single point in time — typically the last day of the reporting period. It answers one question: what does the company own, and how did it pay for those things? The fundamental equation is: Assets = Liabilities + Shareholders' Equity. This equation must always balance — without exception.

Assets are everything the company owns or is owed. Current assets include cash, accounts receivable (money owed by customers), and inventory — items that will be converted to cash within one year. Non-current assets include property, plant, equipment, and intangible assets like patents and goodwill — things the company holds for long-term use. The more liquid the asset (closer to cash), the easier it is to meet short-term obligations.

Liabilities are everything the company owes. Current liabilities — accounts payable, short-term debt, accrued expenses — must be repaid within a year. Non-current liabilities include long-term debt and deferred tax. Shareholders' equity is the residual: what belongs to shareholders after all liabilities are paid. It equals the company's total assets minus its total liabilities. A growing shareholders' equity over time, alongside growing earnings, is a hallmark of a quality business."""
    ),

    ("Reading Financial Statements", "Current vs Non-Current Assets"): (
        IMG + "1551288049-bebda4e38f71" + W,
        """The distinction between current and non-current assets is vital for assessing a company's short-term financial health. Current assets are those expected to be converted into cash or used up within one year: cash and cash equivalents, marketable securities, trade receivables, inventories, and prepaid expenses. These assets fund the company's day-to-day operations.

Non-current assets — sometimes called long-term or fixed assets — have a useful life beyond one year. They include property, plant, and equipment (PP&E), intangible assets (patents, trademarks, goodwill), long-term investments, and deferred tax assets. PP&E is typically depreciated over its useful life, so the balance sheet value gradually declines even if the physical asset is in perfect condition.

The Current Ratio = Current Assets ÷ Current Liabilities measures whether a company can cover its short-term obligations with short-term assets. A ratio above 1.5 is generally considered healthy. The Quick Ratio (or Acid Test) is more conservative: (Current Assets − Inventory) ÷ Current Liabilities. Inventory can take time to sell, so excluding it gives a tighter measure of immediate liquidity. Companies with strong cash positions and low short-term debt are best positioned to withstand economic downturns."""
    ),

    ("Reading Financial Statements", "The Cash Flow Statement"): (
        IMG + "1526304640581-d334cdbbf45e" + W,
        """Profits can be manufactured through accounting choices; cash is far harder to fake. The cash flow statement tracks actual cash entering and leaving the business during the period, divided into three activities: Operating, Investing, and Financing.

Cash from Operating Activities (CFO) measures the cash generated by the core business — selling products and services. This is the most important section. A profitable company with consistently negative operating cash flow is a red flag: it may be recognising revenue before collecting cash, or spending heavily on working capital. Great businesses generate CFO well in excess of net profit year after year.

Cash from Investing Activities covers capital expenditure (buying property, plants, equipment), acquisitions, and disposals. Heavy negative investing cash flow is not automatically bad — it may mean the company is investing aggressively in growth. Cash from Financing Activities covers debt raised or repaid, equity issued, and dividends paid. Cash a company borrows from banks shows up here. Taken together, these three sections explain the net change in cash during the period — and reveal whether the business is self-funding or dependent on external capital to survive."""
    ),

    ("Reading Financial Statements", "Key Financial Ratios"): (
        IMG + "1551288049-bebda4e38f71" + W,
        """Financial ratios compress the information in three financial statements into a single number that is easy to compare. The Price-to-Earnings ratio (P/E) = Market Price per Share ÷ Earnings per Share. It tells you how many years of current earnings you are paying for. A P/E of 25 means the market is willing to pay 25 times annual earnings — typically reflecting expectations of strong future growth.

Return on Equity (ROE) = Net Income ÷ Shareholders' Equity. A consistently high ROE (above 15%) suggests management is making excellent use of every rupee shareholders have entrusted to them. Debt-to-Equity = Total Debt ÷ Total Shareholders' Equity. High D/E ratios amplify both gains and losses — great in booms, dangerous in downturns. The Interest Coverage Ratio = EBIT ÷ Interest Expense measures how comfortably the company can pay its interest. Below 1.5 is a warning zone.

No ratio should be read in isolation. Compare ratios over time (is the trend improving?), against industry peers (is the company above or below average?), and against your own investment thesis (what were you expecting?). Ratios are questions, not answers — a high P/E demands an explanation, not automatic rejection."""
    ),

    ("Reading Financial Statements", "Putting It All Together"): (
        IMG + "1454165804606-c3d57bc86b40" + W,
        """Reading financial statements well is less about memorising formulas and more about learning to ask the right questions. Start with the P&L: Is revenue growing? Are margins expanding or contracting? Is net profit growing faster or slower than revenue? Then move to the balance sheet: Is debt increasing? Is cash growing? Is working capital being managed well?

Finally, validate everything with the cash flow statement. A company reporting strong profits but generating little or negative operating cash flow is showing you a discrepancy — investigate why. On the other hand, a company that consistently converts a high proportion of its net profit into operating cash flow (high cash conversion ratio) is demonstrating that its profits are real.

Practice on companies you know. Pull the annual report of a consumer brand or technology company you are familiar with, read the three statements, and compute the key ratios. Compare to the previous year. Compare to a competitor. Your pattern recognition will improve dramatically after just a few sessions, and you will start reading the stock market with a clarity that most casual investors never develop."""
    ),

    ("Reading Financial Statements", "Common Red Flags"): (
        IMG + "1504711434969-e33886168f5c" + W,
        """Experienced investors know that financial statements can hide trouble just as effectively as they reveal it. Here are the most important red flags to watch for. Rising debt relative to equity or earnings, especially in a slowing-revenue environment, signals a company funding operations with borrowing — unsustainable long-term. Negative operating cash flow despite reported profits means cash is leaking somewhere: either customers are not paying, or inventory is piling up unsold.

Frequent "one-time" or "exceptional" charges are another warning sign. Every company faces occasional write-offs, but a company that reports exceptional charges every single quarter is using them to hide recurring expenses. Rapidly rising accounts receivable relative to revenue suggests the company is booking revenue for sales it has not yet collected — an aggressive accounting practice that inflates profits temporarily.

Auditor qualifications are serious. If the statutory auditor flags concerns in their report, or if the company switches auditors frequently, treat it as a major warning. Promoter pledging of shares — where company founders use their own shares as collateral for loans — suggests the promoters need cash urgently and is a common precursor to corporate governance failures in Indian markets. Always read the notes to the financial statements and the auditor's report, not just the headline numbers."""
    ),

    ("Reading Financial Statements", "Summary & Key Takeaways"): (
        IMG + "1568515387631-8b650bbcdb90" + W,
        """You now have a solid foundation for reading company financials. The three statements work together: the P&L shows profitability over a period, the Balance Sheet shows financial position at a point in time, and the Cash Flow Statement confirms whether profits are being converted to real cash. Together they paint a complete picture no single document can provide.

Remember the key ratios: P/E for valuation, ROE for management efficiency, D/E for leverage, current ratio for liquidity, and cash conversion ratio for earnings quality. No ratio means anything in isolation — always compare over time, against peers, and against your own assumptions when you made the investment.

The most important habit a fundamental investor can develop is reading annual reports — not just the headline numbers, but the Management Discussion & Analysis section, the notes to accounts, and the auditor's report. Companies that communicate openly about risks and challenges are generally governed better than those that only trumpet successes. Treat financial statements as a conversation with the business — and listen carefully."""
    ),

    # ── Module 4: Risk & Risk Management ─────────────────────────
    ("Risk & Risk Management", "What Is Risk?"): (
        IMG + "1611974789855-9c2a0a7236a3" + W,
        """In everyday language, risk means danger. In finance, risk has a more precise definition: it is the possibility that an investment's actual return will differ from its expected return. This includes returns that are lower than expected — but also, in theory, returns that are higher. Standard financial theory measures risk using statistical volatility: how widely actual returns are dispersed around the average.

Risk in investing takes many forms. Some risks are specific to a single company (business risk, management risk, fraud risk) and can be diversified away by holding many investments. Others are market-wide — recession risk, interest rate risk, inflation risk — and affect nearly all investments simultaneously and cannot be eliminated through diversification. Understanding which risk you are taking on is the first step to managing it.

An important insight from modern portfolio theory: you are not compensated for risks you could have diversified away. If you own only one stock and it crashes, the market does not care — you took unnecessary concentration risk. The market compensates you only for bearing market-wide (systematic) risk. This is the rationale for diversification: eliminate the risks you are not being paid to take."""
    ),

    ("Risk & Risk Management", "Types of Risk"): (
        IMG + "1526304640581-d334cdbbf45e" + W,
        """Market risk (systematic risk) is the risk that the entire market declines, dragging your portfolio with it. This happened in 2008 (Global Financial Crisis), 2020 (COVID crash), and in every bear market in history. Diversification does not protect you here — only correct asset allocation (holding some cash or bonds) provides a partial buffer.

Credit risk is the risk that a borrower (company or government) fails to make interest or principal payments. Relevant when investing in corporate bonds or debt funds. Liquidity risk is the risk that you cannot sell your investment quickly at a fair price — common in small-cap stocks, real estate, and some fixed deposits. Concentration risk arises from over-exposure to one stock, sector, or geography — your risk becomes correlated with a single outcome.

Inflation risk is subtle but powerful: even if your investment returns 6%, you are losing purchasing power if inflation is running at 7%. Real return = Nominal Return − Inflation. Regulatory and political risk — policy changes, tax law amendments, or government intervention — can dramatically affect entire sectors overnight, as Indian investors in the ed-tech and cryptocurrency spaces discovered in 2021. Currency risk matters for international investments: a 10% gain in a US stock is wiped out if the USD weakens 10% against the INR."""
    ),

    ("Risk & Risk Management", "Measuring Risk — Volatility & Beta"): (
        IMG + "1642543492481-44e81e3914a7" + W,
        """Standard deviation measures how much a stock's or portfolio's returns vary around the average. A stock with an average annual return of 12% and a standard deviation of 5% typically produces returns between 7% and 17% in most years. A stock with the same average but a standard deviation of 30% might return anywhere from −18% to +42%  — far more uncertain. Higher standard deviation means higher volatility, which most investors equate with higher risk.

Beta measures a stock's sensitivity to market movements. A beta of 1.0 means the stock moves in line with the market. A beta of 1.5 means the stock tends to rise 15% when the market rises 10%, and fall 15% when the market falls 10%. A beta below 1.0 indicates the stock is less volatile than the market — defensives like utilities and FMCG companies typically have low betas. Negative-beta assets (very rare) move opposite to the market.

Beta is useful for portfolio construction: if you want to reduce your portfolio's overall sensitivity to market swings, add lower-beta stocks. If you want to amplify gains in a bull market (while accepting larger losses in a bear market), add higher-beta stocks. Neither approach is inherently right — it depends on your time horizon, risk tolerance, and current life situation."""
    ),

    ("Risk & Risk Management", "Stop-Loss Orders"): (
        IMG + "1590283603385-17ffb3a7f29f" + W,
        """A stop-loss is an instruction to your broker to automatically sell a stock if the price falls to a specified level. If you buy a stock at ₹200 and set a stop-loss at ₹180, your broker will execute a sell order the moment the stock trades at ₹180 or below. This caps your maximum loss at 10% of the trade and prevents a temporary setback from becoming a permanent loss of capital.

Stop-losses are particularly important for traders and investors who take concentrated positions. Without a stop-loss, a 30% loss requires a 43% gain just to break even; a 50% loss requires a 100% gain. Stop-losses also help manage psychology: with a pre-defined exit point, you remove the need to make a decision under pressure when the market is falling and fear is highest.

The downside of stop-losses is the risk of being "stopped out" by temporary volatility. A stock might fall to your stop-loss level due to intraday noise, trigger a sell, and then recover immediately. For long-term investors in fundamentally strong companies, tight stop-losses can be counterproductive. The solution is to use wider stop-losses for long-term positions (e.g., 20–25% below cost) and tighter ones for short-term trades (5–10%), calibrated to the expected volatility of each position."""
    ),

    ("Risk & Risk Management", "Position Sizing"): (
        IMG + "1579621970588-a35d0e7ab9b6" + W,
        """Position sizing answers the question: "How much of my portfolio should I allocate to this single investment?" It is one of the most important — and most underrated — risk management tools available to investors. No matter how convinced you are of an investment thesis, concentrating too much in a single position creates the possibility of severe, potentially unrecoverable losses.

A common rule of thumb among professional traders is the 2% rule: never risk more than 2% of your total portfolio on any single trade. "Risk" here specifically means potential loss — defined by your stop-loss distance. If your portfolio is ₹10 lakh and you are willing to risk 2%, your maximum loss per trade is ₹20,000. If you are buying at ₹200 with a stop-loss at ₹180 (₹20 per share risk), you should buy at most 1,000 shares (₹20,000 ÷ ₹20).

For long-term investors (not traders), a rough guideline is to keep no single stock above 5–10% of the portfolio, no single sector above 25–30%, and always hold at least some liquidity for opportunities and emergencies. Position sizing is not about being timid — it is about staying in the game long enough for your best ideas to work. Many talented investors have been wiped out not because they were wrong about a stock, but because they bet too much of their capital on a single outcome."""
    ),

    ("Risk & Risk Management", "Diversification as Risk Management"): (
        IMG + "1466354424719-343280fe118b" + W,
        """We introduced diversification in the Mutual Funds module as a feature of pooled investment vehicles. Here we examine it as an explicit risk management strategy. The mathematical principle: when you combine assets whose returns are not perfectly correlated, the portfolio's volatility is lower than the weighted average volatility of its individual components. This is the only "free lunch" in finance — you reduce risk without necessarily reducing expected return.

Effective diversification spans multiple dimensions. Asset class diversification (equities + bonds + gold + real estate) protects against class-specific catastrophes. Sector diversification (technology + banking + pharma + consumer goods) protects against sector-specific downturns — regulations, input price shocks, or disruption. Geographic diversification (India + international) protects against country-specific risks like political instability or currency devaluation.

Research suggests that most of the benefits of stock diversification within a single asset class are captured by holding 20–30 different stocks across sectors. Beyond that, adding more stocks does not significantly reduce risk but does add complexity. The key is ensuring your holdings are genuinely different — owning 30 IT stocks instead of one does not provide meaningful diversification since they are all exposed to the same risks (rupee appreciation, US visa policy, global tech spending trends)."""
    ),

    ("Risk & Risk Management", "Risk-Reward Ratio"): (
        IMG + "1611974789855-9c2a0a7236a3" + W,
        """Before entering any investment or trade, one of the most useful questions to ask is: "What is my upside, and what is my downside?" The risk-reward ratio formalises this: Potential Reward ÷ Potential Risk. A 2:1 ratio means you stand to gain ₹2 for every ₹1 you risk; a 3:1 ratio means you gain ₹3 for every ₹1 at risk.

Why does this matter? Even if you are right only 50% of the time, a consistent 2:1 risk-reward ratio makes you profitable overall. Over 10 trades where you are correct 5 times and wrong 5 times: 5 wins × ₹2 = ₹10 gained; 5 losses × ₹1 = ₹5 lost. Net profit: ₹5 on a ₹1 base risk per trade. This mathematics of asymmetric bets is why disciplined traders can be right less than half the time and still build wealth.

For long-term investors, risk-reward thinking manifests as valuation: buying a stock when it trades well below intrinsic value (large margin of safety) creates an asymmetric opportunity — limited downside if you are wrong, large upside if you are right. Conversely, buying a stock at a stretched valuation gives you enormous downside if the company disappoints, with limited further upside even if it delivers perfectly. Always seek asymmetry: situations where you risk little to potentially gain a lot."""
    ),

    ("Risk & Risk Management", "Summary & Key Takeaways"): (
        IMG + "1504711434969-e33886168f5c" + W,
        """Risk management is not about avoiding risk — it is about taking the right risks in the right amounts. Every excess return above the risk-free rate requires accepting some form of risk. The goal is to maximise the return you earn per unit of risk accepted, not to eliminate risk entirely.

The tools you now have: diversification (to eliminate unsystematic risk), position sizing (to cap the damage of any single mistake), stop-loss orders (to enforce discipline and prevent small losses from becoming catastrophic ones), understanding beta and standard deviation (to choose investments appropriately for your goals), and the risk-reward ratio (to ensure every bet you take is mathematically favourable given your win rate).

Apply these principles consistently. Most investment disasters are not caused by choosing the wrong stock — they are caused by putting too much money into a single stock, failing to cut a loss when the thesis proved wrong, or chasing a position purely on excitement without understanding the downside. Risk management is the unsexy work that separates successful long-term investors from those who flame out early."""
    ),
}


class Command(BaseCommand):
    help = "Enrich lesson content with multi-paragraph text and image URLs."

    def handle(self, *args, **options):
        updated = 0
        not_found = 0

        for (module_title, lesson_title), (image_url, content) in LESSON_ENRICHMENT.items():
            try:
                module = Module.objects.get(title=module_title)
            except Module.DoesNotExist:
                self.stdout.write(self.style.WARNING(f"  Module not found: {module_title}"))
                not_found += 1
                continue

            rows = Lesson.objects.filter(module=module, title=lesson_title).update(
                content=content,
                image_url=image_url,
            )
            if rows:
                updated += rows
            else:
                self.stdout.write(self.style.WARNING(f"  Lesson not found: {lesson_title} in {module_title}"))
                not_found += 1

        self.stdout.write(self.style.SUCCESS(f"✔ Enriched {updated} lessons. {not_found} not found."))

# ── Module 5–8 enrichment (appended) ────────────────────────────────────────
LESSON_ENRICHMENT.update({

    # ── Module 5: Technical Analysis Basics ──────────────────────
    ("Technical Analysis Basics", "What Is Technical Analysis?"): (
        IMG + "1551288049-bebda4e38f71" + W,
        """Technical analysis (TA) is the study of past market data — primarily price and volume — to forecast future price movements. Unlike fundamental analysis, which asks "what is this company worth?", technical analysis asks "what will this stock's price do next, based on observable market behaviour?" The core assumption is that all publicly known information is already reflected in the price, and that patterns of human behaviour repeat in predictable ways.

TA has its roots in the writings of Charles Dow (of Dow Jones fame) in the late 19th century. Today it is used by millions of traders worldwide, from day traders watching one-minute candles to institutional fund managers analysing weekly charts. Its tools — candlestick patterns, trendlines, moving averages, momentum oscillators — provide a common language for interpreting market psychology.

It is important to understand what technical analysis is not: it is not fortune-telling, and it does not work 100% of the time. It provides probabilities, not certainties. No indicator is right more than 60–70% of the time in well-designed systems, and many retail traders lose money using TA incorrectly. Used with discipline, clear rules, and proper risk management, technical analysis can be a powerful supplement to — or substitute for — fundamental analysis, depending on your trading timeframe."""
    ),

    ("Technical Analysis Basics", "Candlestick Charts"): (
        IMG + "1611974789855-9c2a0a7236a3" + W,
        """Candlestick charts were developed in 18th-century Japan by rice traders and brought to the West by Steve Nison in the 1990s. Each candle represents price action over a defined period — one minute, one hour, one day, one week — and encodes four pieces of data: the opening price, the closing price, the highest price reached (high), and the lowest price reached (low).

The "body" of the candle is the rectangle between the open and close. A green (or white) body means the price closed higher than it opened — bullish. A red (or black) body means the price closed lower than it opened — bearish. The thin lines extending above and below the body are called wicks or shadows; the upper wick shows how high price reached before being rejected, and the lower wick shows how low it went before buyers stepped in.

Individual candlestick patterns carry meaning. A "doji" (tiny body, long wicks) signals indecision. A "hammer" (small body, long lower wick) at the bottom of a downtrend signals potential reversal as buyers fought back aggressively. An "engulfing" pattern — where one large candle completely covers the previous candle's body — signals a powerful shift in momentum. Multi-candle patterns (morning star, evening star, three white soldiers) provide even stronger signals. Always confirm candle signals with volume and trend context."""
    ),

    ("Technical Analysis Basics", "Support & Resistance"): (
        IMG + "1642543492481-44e81e3914a7" + W,
        """Support is a price level where a falling stock tends to pause or reverse upward, because buyers consider it an attractive price and step in to purchase. Resistance is the mirror image — a level where a rising stock tends to stall or reverse downward, because sellers consider it a fair price to exit. These levels form because human memory is persistent: traders remember where a stock previously bounced or reversed, and those prices become self-fulfilling reference points.

When a resistance level is broken convincingly (on high volume, with the price closing above it), that level often flips to become support — a concept known as "role reversal." The more times a level has been tested without being broken, the stronger it is considered. Round numbers (₹500, ₹1000, ₹100) are particularly powerful support and resistance levels because they attract large amounts of limit orders.

Support and resistance are not precise price points but zones. A stock that "bounced off ₹450 support" three times might actually have bounced from anywhere between ₹445 and ₹455. Trade the zone, not the exact number. When the price is between well-defined support and resistance (called a "range"), traders can buy near support and sell near resistance. When price breaks out of the range with conviction, it may launch a sustained trend in the breakout direction."""
    ),

    ("Technical Analysis Basics", "Trend Lines & Channels"): (
        IMG + "1551288049-bebda4e38f71" + W,
        """A trendline is a straight line drawn on a chart connecting a series of price points to identify the direction of a trend. In an uptrend, you connect successive higher lows — each dip is bought at a higher price than the last, creating an ascending support line. In a downtrend, you connect successive lower highs — each rally is sold at a lower price, creating a descending resistance line.

A valid trendline must be touched at least three times to be considered meaningful (two points define any line; the third point validates it). When a stock reaches its upward trendline and bounces, that is a potential buying opportunity. When it breaks below the trendline on strong volume, the uptrend may be ending — a sell signal. The slope of the trendline also matters: very steep trendlines are typically unsustainable and more likely to break.

When two parallel trendlines — one acting as support, one as resistance — contain price action, the result is a price channel. Price oscillates between the two lines in a predictable rhythm. Traders can buy at the channel support and sell at the channel resistance. A breakout from the channel — above or below — often leads to acceleration in the breakout direction, with the channel's width providing a guide to the magnitude of the expected move."""
    ),

    ("Technical Analysis Basics", "Moving Averages"): (
        IMG + "1526304640581-d334cdbbf45e" + W,
        """A moving average (MA) smooths out price data by averaging closing prices over a defined look-back period, removing day-to-day noise. The Simple Moving Average (SMA) gives equal weight to all periods. The Exponential Moving Average (EMA) gives more weight to recent prices, making it more responsive to current market conditions. A 20-day EMA, for instance, reacts faster to new price swings than a 20-day SMA.

Moving averages serve multiple purposes. They identify the trend: price consistently above the MA signals an uptrend; below, a downtrend. They act as dynamic support and resistance: in an uptrend, price often dips to the 50-day MA before bouncing, providing a lower-risk entry. They generate crossover signals: when a shorter MA crosses above a longer MA (e.g., the 50-day crossing the 200-day), it is called a "golden cross" — a bullish signal. The reverse (50-day crossing below the 200-day) is a "death cross" — bearish.

The most widely watched MAs are the 20-day (short-term trend), 50-day (medium-term trend), and 200-day (long-term trend). In Indian markets, many traders also use 9-day and 21-day EMAs for short-term signals. Moving averages are lagging indicators — they confirm trend changes after they have begun, never before — so they are best combined with leading indicators (like price patterns and volume) for more complete analysis."""
    ),

    ("Technical Analysis Basics", "Volume Analysis"): (
        IMG + "1590283603385-17ffb3a7f29f" + W,
        """Volume — the number of shares traded during a period — is the fuel that powers price movements. Price moves on high volume are more significant and more likely to sustain than price moves on thin volume. Think of volume as the crowd's conviction: a stock rising on record volume signals that masses of buyers are participating enthusiastically; rising on low volume suggests the move is tentative and may not last.

The key principle: price and volume should confirm each other. Rising prices + rising volume = healthy uptrend (demand is genuine). Rising prices + falling volume = weakening trend, watch for reversal. Falling prices + rising volume = strong selling pressure, downtrend likely continues. Falling prices + falling volume = selling is exhausting, a reversal may be near. A volume spike on a breakout from a range or pattern is perhaps the most bullish single candle you can see — it signals institutional buying.

Volume indicators formalise this analysis. On-Balance Volume (OBV) adds volume on up days and subtracts volume on down days, creating a running total. When OBV rises with price, buying pressure is accumulating. When OBV diverges from price (price rises but OBV falls), the rally may lack institutional support. The Volume Weighted Average Price (VWAP) calculates the average price weighted by volume throughout the day — widely used by institutional traders as a benchmark."""
    ),

    ("Technical Analysis Basics", "RSI — Relative Strength Index"): (
        IMG + "1579621970588-a35d0e7ab9b6" + W,
        """The Relative Strength Index (RSI), developed by J. Welles Wilder in 1978, is a momentum oscillator that measures the speed and magnitude of recent price changes. It ranges from 0 to 100. Historically, a reading above 70 is considered overbought — the stock has risen too fast and may be due for a pullback. A reading below 30 is considered oversold — the stock has fallen too fast and may be due for a bounce.

RSI is calculated by comparing the average of up-closes to the average of down-closes over a lookback period (typically 14 days). RSI = 100 − (100 ÷ (1 + RS)), where RS = Average Gain ÷ Average Loss. The formula ensures the indicator stays within the 0–100 band. In strong uptrends, RSI often lives between 50 and 80 without reaching 30 — so context matters: what is "overbought" in a sideways market may be "normal" in a strong bull market.

One of the most powerful RSI signals is divergence. Bullish divergence occurs when the price makes a lower low but RSI makes a higher low — suggesting selling momentum is exhausting even as price falls further. This often precedes a reversal upward. Bearish divergence is the mirror: price makes a higher high but RSI makes a lower high, suggesting the rally is running out of momentum. Divergences are not precise timing tools but are important early warning signals."""
    ),

    ("Technical Analysis Basics", "MACD Indicator"): (
        IMG + "1466354424719-343280fe118b" + W,
        """MACD (Moving Average Convergence Divergence), created by Gerald Appel in 1979, is one of the most widely used momentum and trend-following indicators. It is built from three components: the MACD line (12-day EMA minus 26-day EMA), the Signal line (9-day EMA of the MACD line), and the Histogram (MACD minus Signal line, visualised as bars above and below zero).

When the MACD line crosses above the Signal line, it generates a bullish crossover signal — momentum is shifting upward. When it crosses below, it is a bearish signal. The Histogram shows the strength and direction of the momentum: large positive bars indicate strong upward momentum; large negative bars indicate strong downward pressure; bars shrinking toward zero suggest the trend is losing steam and a crossover may be coming.

The MACD zero line is also significant. When MACD crosses above zero, the 12-day EMA has crossed above the 26-day EMA — a broader bullish signal. When it crosses below zero, bearish. Like RSI, MACD divergence is important: if price makes new highs but MACD makes lower highs, that negative divergence warns the rally may be fading. MACD is best used on daily or weekly charts for swing trading, and works poorly in choppy, sideways markets where it generates false signals repeatedly."""
    ),

    ("Technical Analysis Basics", "Chart Patterns"): (
        IMG + "1614728894747-a83421e2b9c9" + W,
        """Chart patterns are recurring geometric formations in price charts that signal either a continuation of the existing trend or a reversal. They form because collective human psychology produces predictable responses to specific price structures. Learning to recognise them — and distinguishing high-probability patterns from random noise — is one of the most valuable skills in technical analysis.

Reversal patterns signal that the existing trend is ending. The Head and Shoulders pattern (a peak, a higher peak, then a lower peak, with a "neckline" connecting the troughs) is among the most reliable reversal patterns — when price breaks below the neckline after forming the right shoulder, it signals the uptrend is over. Double Top (two peaks at similar prices) and Double Bottom (two troughs) are simpler versions signalling reversal. Rounding tops and bottoms are longer, more gradual reversals.

Continuation patterns signal a temporary pause before the trend resumes. Triangles (symmetrical, ascending, descending) form as price consolidates into a narrowing range before breaking out in the original direction. Flags and pennants are brief, tight consolidations after a strong directional move — like a flag on a flagpole — that typically resolve with a continuation of the prior move. Always wait for a confirmed breakout from a pattern (typically a close beyond the breakout level on higher volume) before acting."""
    ),

    ("Technical Analysis Basics", "Summary & Key Takeaways"): (
        IMG + "1504711434969-e33886168f5c" + W,
        """Technical analysis provides a toolkit for reading market psychology through price and volume. No single indicator is sufficient — the power lies in confluence: when candlestick patterns, support/resistance, moving averages, volume, and momentum oscillators all point in the same direction simultaneously, the probability of the trade working significantly increases.

Remember the key tools you have learned: candlesticks encode the battle between buyers and sellers in each period; support and resistance mark the price levels where the crowd has previously made decisions; moving averages identify the trend and provide dynamic support; RSI and MACD measure momentum and generate divergence signals; chart patterns provide structured entry and exit points.

Be cautious of overconfidence. Technical analysis is a probabilistic skill that takes years of screen time to develop. Paper-trade your ideas before risking real capital. Keep a trading journal to track which setups work for you in which market conditions. No indicator works in all markets all the time — the best traders use TA with clear rules, strict risk management, and the humility to accept small losses quickly before they become large ones."""
    ),

    # ── Module 6: Fundamental Analysis ───────────────────────────
    ("Fundamental Analysis", "What Is Fundamental Analysis?"): (
        IMG + "1568515387631-8b650bbcdb90" + W,
        """Fundamental analysis (FA) is a method of evaluating a security by examining the underlying financial and economic factors that affect a company's intrinsic value. Rather than studying price charts and trading patterns, a fundamental analyst asks: Is this business profitable? Is it growing? Is it managed well? Does it have a durable competitive advantage? And most importantly: is the current stock price above or below what the business is actually worth?

FA is the approach championed by investment legends like Benjamin Graham (who wrote "The Intelligent Investor"), Warren Buffett, and Peter Lynch. Graham's "Mr Market" allegory captures its philosophy beautifully: the stock market is like an emotional business partner who offers to buy or sell his share of the business every day at wildly fluctuating prices. Your job is not to follow Mr Market's moods, but to wait patiently until his price is far below the business's true worth.

FA combines quantitative analysis (financial ratios, growth rates, cash flows) with qualitative analysis (management quality, competitive moats, industry trends). It is best suited for investors with long time horizons — months to years — because it ignores short-term price fluctuations and focuses on whether the underlying business will be worth more in the future. Done correctly, it gives investors both the conviction to buy and the patience to hold through inevitable market volatility."""
    ),

    ("Fundamental Analysis", "Intrinsic Value & Margin of Safety"): (
        IMG + "1579621970588-a35d0e7ab9b6" + W,
        """Intrinsic value is the true economic value of a business — what a rational, fully informed buyer would pay for the entire company if it were a private business rather than a stock. Estimating it requires projecting future earnings or cash flows and discounting them back to today at an appropriate rate. It is inherently imprecise — different analysts will arrive at different intrinsic values — but the range of reasonable estimates is still useful for making buy/sell decisions.

The margin of safety, a concept popularised by Benjamin Graham, is the gap between the stock's current market price and your estimate of its intrinsic value. If you estimate a stock is worth ₹1,000 and it trades at ₹600, you have a 40% margin of safety. This buffer protects you against errors in your analysis, unforeseen business deterioration, or plain bad luck. The larger the margin of safety, the smaller the possible permanent loss of capital.

Margin of safety is not just a defensive concept — it is also the source of outsized returns. Buying ₹1 of value for ₹0.60 creates an asymmetric bet: if you are right, the market eventually recognises fair value and your investment rises 67%. If you are somewhat wrong in your intrinsic value estimate, the discount means you may still break even or earn a modest profit. This asymmetry — limited downside, large upside — is the hallmark of great value investments."""
    ),

    ("Fundamental Analysis", "Price-to-Earnings (P/E) Ratio"): (
        IMG + "1642543492481-44e81e3914a7" + W,
        """The Price-to-Earnings ratio is the most widely quoted valuation metric in global markets. P/E = Current Market Price per Share ÷ Earnings per Share (EPS). It answers the question: "How many years of current earnings am I paying for?" A P/E of 20 means the stock's total price equals 20 years of current annual earnings — a high expectation of future growth embedded in the price.

P/E ratios vary widely by sector. Banks and utilities typically trade at 10–15x earnings because their growth is moderate and predictable. Fast-growing technology or FMCG companies can trade at 40–60x or more, because investors price in years of future earnings growth. This is why you must always compare P/E within the same sector and peer group — a software company at P/E 40 may be cheap compared to peers at 60, while a steel company at P/E 16 may be expensive if peers trade at 8.

Two important variants: Trailing P/E uses the earnings from the past 12 months (known, but backward-looking). Forward P/E uses analyst estimates of next year's earnings (more relevant, but depends entirely on accurate forecasts). A high P/E is not automatically a sell — if earnings are growing rapidly, the high current P/E may be justified by much larger earnings in future years. Always ask: "What earnings growth rate does this P/E imply, and is that growth rate realistic and sustainable?" """
    ),

    ("Fundamental Analysis", "Price-to-Book (P/B) Ratio"): (
        IMG + "1526304640581-d334cdbbf45e" + W,
        """The Price-to-Book ratio compares a stock's market price to its book value per share. Book value is shareholders' equity per share — the accounting value of what shareholders own after all liabilities are paid. P/B = Market Price per Share ÷ Book Value per Share. A P/B of 3x means the market values the company at three times its accounting net worth.

P/B below 1 used to be Benjamin Graham's primary screening criterion. In theory, a P/B < 1 means you are buying assets for less than their accounting value — a seemingly attractive deal. In practice, accounting values can be misleading: a company with lots of fixed assets that are overvalued on the balance sheet, or goodwill from overpriced acquisitions, may have a deceptively high book value. Conversely, technology and service companies whose primary assets are human capital and brand reputation may have very little tangible book value — their P/B will be high not because they are expensive, but because their most valuable assets are intangible.

P/B is most useful for financial companies (banks, NBFCs, insurance companies) where the balance sheet is the primary business — loans and deposits are what matter. A bank trading at 1x book is very different from one trading at 4x book, and the difference reflects expected future return on equity. For asset-light technology businesses, P/B is far less informative and should be supplemented with other metrics."""
    ),

    ("Fundamental Analysis", "Return on Equity (ROE)"): (
        IMG + "1554224155-6726b3ff858f" + W,
        """Return on Equity measures how efficiently a company uses shareholders' money to generate profit. ROE = Net Income ÷ Average Shareholders' Equity, expressed as a percentage. A company with ₹100 crore in equity and ₹20 crore in net profit has an ROE of 20% — meaning it generates ₹20 of profit for every ₹100 shareholders have invested. Consistently high ROE over many years is one of the strongest signals of a quality business.

Warren Buffett has said that one of his primary screens for investment candidates is ROE above 15% for at least 10 consecutive years. Why does sustained ROE matter more than a single year's figure? Because a one-time win (asset sale, tax benefit) can spike ROE for a single year. Sustained ROE above the cost of equity — maintained year after year across business cycles — demonstrates a genuine structural advantage that competitors cannot easily replicate.

The DuPont Analysis breaks ROE into three components: Net Profit Margin × Asset Turnover × Financial Leverage. This decomposition is revealing. A company can have high ROE by being very profitable (high margins), by being very efficient (high asset turnover — like a retailer that moves lots of inventory on little capital), or by using significant debt (high leverage). ROE driven by margin and efficiency is sustainable and healthy; ROE driven primarily by leverage is fragile and risky, especially in rising interest rate environments."""
    ),

    ("Fundamental Analysis", "Economic Moats"): (
        IMG + "1466354424719-343280fe118b" + W,
        """Warren Buffett coined the term "economic moat" to describe a business's durable competitive advantages — the structural barriers that protect its profits from competitors, just as a medieval castle's moat protected it from attack. Companies with wide moats can maintain pricing power, high margins, and strong returns on capital for decades. Without a moat, even attractive businesses eventually see their profits competed away.

The main sources of economic moats are: Intangible assets — brand names, patents, regulatory licenses that competitors cannot easily replicate. Coca-Cola's brand allows it to charge a premium for flavoured sugar water. Network effects — the product becomes more valuable as more users join. Facebook, WhatsApp, and stock exchanges all benefit from network effects. Cost advantages — through scale, superior processes, or proprietary technology, some companies simply produce goods cheaper than any competitor could. Switching costs — high friction in moving from one product to another locks in customers. Think of how difficult it is to migrate your banking, or to switch away from deeply embedded enterprise software.

Identifying moats requires qualitative judgment: Can a well-funded competitor replicate this company's advantage with enough time and money? If a large company threw ₹10,000 crore at competing with this business, would it succeed? Companies where the answer is clearly "no" possess genuine moats. Moats erode over time through technology disruption, regulatory change, and competitor innovation — so even moated businesses require ongoing monitoring."""
    ),

    ("Fundamental Analysis", "Management Quality"): (
        IMG + "1454165804606-c3d57bc86b40" + W,
        """Even the best business can be destroyed by poor management, and a mediocre business can generate excellent returns under exceptional leadership. Assessing management quality is a qualitative skill, but there are concrete factors to examine. Capital allocation is paramount: does management invest retained earnings wisely? Have past acquisitions created value or destroyed it? Do they return excess capital to shareholders through buybacks and dividends when growth opportunities are scarce?

Track record matters enormously. How has management navigated previous downturns? Have they delivered on past guidance? Do they acknowledge mistakes and explain clearly what went wrong, or do they shift blame and make excuses? A management team that communicates transparently with shareholders — including about challenges and failures — is far preferable to one that only appears in good times.

Insider ownership is a useful alignment signal. When founders and executives own significant amounts of company stock personally (not just through options), their financial interests align with outside shareholders. Watch for insiders selling large amounts of stock, especially when they have simultaneously been publicly bullish on the business. Also examine corporate governance: board independence, related-party transactions, and auditor quality are the institutional safeguards that protect minority shareholders from value extraction by promoters."""
    ),

    ("Fundamental Analysis", "Industry & Competitive Analysis"): (
        IMG + "1590283603385-17ffb3a7f29f" + W,
        """No company exists in a vacuum. Its profitability is heavily influenced by the structure of the industry in which it operates. Michael Porter's Five Forces framework is the standard tool for industry analysis. The five forces are: (1) Competitive rivalry — how intense is competition among existing players? (2) Threat of new entrants — how easy is it for new competitors to enter? (3) Threat of substitutes — can customers switch to a completely different product type? (4) Buyer power — how much negotiating leverage do customers have? (5) Supplier power — how much negotiating leverage do input suppliers have?

An industry with weak competitive rivalry, high barriers to entry, few substitutes, and low buyer and supplier power is an attractive industry to be in — incumbents can earn high margins almost regardless of individual company quality. The Indian telecom industry pre-Jio is an example of an industry that deteriorated rapidly as a powerful new entrant (Reliance Jio) with deep pockets entered and forced massive price wars, destroying margins for everyone.

Beyond Porter's framework, examine the industry's cyclicality, growth rate, regulatory environment, and exposure to technological disruption. A company in a structurally declining industry (physical newspapers, traditional travel agents) will struggle no matter how well managed, while a company in a structurally growing industry (digital payments, healthcare) has a strong tailwind even with mediocre management."""
    ),

    ("Fundamental Analysis", "Valuation Models — DCF Basics"): (
        IMG + "1543286386-713bdd548da4" + W,
        """Discounted Cash Flow (DCF) analysis is the theoretically "correct" way to value any asset: it equals the present value of all future cash flows the asset will generate. The principle: a rupee received today is worth more than a rupee received in the future (because today's rupee can be invested to earn returns). Therefore, future cash flows must be "discounted" back to their present value at an appropriate rate — called the discount rate or required rate of return.

The DCF model has three key inputs: (1) Free Cash Flow (FCF) projections — typically 10 years of explicit forecasts followed by a "terminal value" representing the business in perpetuity. FCF = Operating Cash Flow minus Capital Expenditure. (2) The discount rate — usually the Weighted Average Cost of Capital (WACC), which blends the cost of equity and after-tax cost of debt. A higher discount rate means future cash flows are worth less today. (3) The terminal growth rate — the assumed growth rate in perpetuity beyond the forecast period, usually 2–4%.

The sensitivity of a DCF model to its assumptions is both its power and its weakness. A small change in the discount rate or growth rate dramatically changes the output. An analyst who wants a stock to be cheap will choose optimistic assumptions; one who wants it to be expensive will choose pessimistic ones. This is why thoughtful analysts run multiple scenarios — bull, base, and bear cases — and use the DCF as one input alongside relative valuation metrics rather than as a precise answer."""
    ),

    ("Fundamental Analysis", "Summary & Key Takeaways"): (
        IMG + "1504711434969-e33886168f5c" + W,
        """Fundamental analysis begins with understanding what a business does and how it makes money, then systematically examines whether that business is profitable (P&L), financially healthy (balance sheet), cash generative (cash flow), competitively protected (moat), well-managed (management quality), and attractively priced (valuation). Only when all these factors align is an investment truly compelling.

The key metrics you have learned: P/E for earnings-based valuation; P/B for asset-based valuation; ROE for efficiency of capital use; D/E and interest coverage for leverage assessment; FCF and cash conversion for earnings quality. The key qualitative frameworks: Porter's Five Forces for industry attractiveness; moat analysis for competitive durability; management quality assessment for execution confidence; DCF for intrinsic value estimation.

The final word: great investing is about owning great businesses at fair or cheap prices, then holding them with patience while the business creates value. Fundamental analysis gives you the conviction to hold through inevitable market volatility — because you understand the business well enough to distinguish temporary market pessimism from real business deterioration. That conviction is the real payoff of doing the analytical work."""
    ),

    # ── Module 7: Long-Term Investing Principles ──────────────────
    ("Long-Term Investing Principles", "The Power of Compounding"): (
        IMG + "1559526323-cb2f2fe2591b" + W,
        """Compounding is earning returns not just on your original investment, but on your accumulated returns as well. Albert Einstein allegedly called it "the eighth wonder of the world." Whether or not he actually said it, the mathematics are genuinely extraordinary. ₹1 lakh invested at 12% per year becomes ₹3.1 lakh in 10 years, ₹9.6 lakh in 20 years, and ₹29.9 lakh in 30 years — an increase of nearly 30× from the original investment, with no additional money added.

The three variables that drive compounding are rate of return, time, and the consistency of staying invested. The rate of return matters, but time is the dominant variable. Starting at age 25 instead of age 35 roughly doubles your retirement corpus for the same monthly savings. This is why financial planners universally urge young people to start investing immediately — even small amounts — rather than waiting until they "have more money to invest."

The enemy of compounding is interruption. Every time you withdraw money from an investment, sell in a panic during a market crash, or sit in cash waiting for the "right time" to invest, you reset part of the compounding clock. Studies consistently show that individual investors earn significantly lower returns than the funds they invest in — because they buy after rallies and sell during crashes, precisely when they should do the opposite. The most powerful investing habit: invest regularly, don't touch it, let compounding work."""
    ),

    ("Long-Term Investing Principles", "CAGR — Compound Annual Growth Rate"): (
        IMG + "1526304640581-d334cdbbf45e" + W,
        """CAGR, or Compound Annual Growth Rate, is the single most useful number for comparing investment returns. It smooths out year-to-year volatility to show the steady annual growth rate that would have produced the same outcome. CAGR = (Ending Value ÷ Beginning Value)^(1/n) − 1, where n is the number of years.

Consider a fund that returned +30% in year one, −15% in year two, and +20% in year three. Simple arithmetic gives an average of 11.67% per year. But your actual return if you invested ₹1 lakh: after year 1, ₹1.30 lakh; after year 2, ₹1.105 lakh; after year 3, ₹1.326 lakh. The CAGR = (1.326)^(1/3) − 1 = 9.8% — meaningfully lower than the simple average. This is why CAGR is the correct measure: it accounts for the compounding sequence of actual returns.

When comparing mutual funds, portfolio managers, or investment strategies, always use CAGR over a sufficiently long period — at least 5 years, preferably 10 or more. Short periods are dominated by luck. Over long periods, genuine skill and strategy separate truly superior investors from those who simply had a lucky run. A fund with CAGR of 14% over 15 years has almost certainly demonstrated real skill; one with 14% CAGR over 2 years may simply have caught a bull market."""
    ),

    ("Long-Term Investing Principles", "SIP vs Lump Sum"): (
        IMG + "1614728894747-a83421e2b9c9" + W,
        """Both SIP (Systematic Investment Plan) and lump sum are valid investment strategies — the best choice depends on your financial situation and market context. A lump sum investment deploys all available capital at once. This is mathematically optimal if you invest at the start of a sustained bull market, because your full corpus compounds from day one. If you invest at a market peak, however, you may sit in loss for years before recovering.

SIP spreads investments over time, automatically buying more units when prices are low and fewer when prices are high — rupee-cost averaging in action. This averaging effect reduces the impact of mistimed entry. SIP is not always mathematically superior to lump sum — in a steadily rising market, lump sum wins historically about 66% of the time because the market goes up more often than it goes down. But SIP wins on the psychological dimension: it is far easier to commit to regular small investments than to muster the courage for a large one-time commitment.

For salaried investors, the question is largely settled: your salary arrives monthly, so SIP naturally matches your cash flow. Invest a fixed amount on your salary date before any discretionary spending (the "pay yourself first" principle). For investors receiving a windfall (inheritance, bonus, asset sale), the choice between immediate lump sum and systematic staggered investment depends on their emotional resilience, current market valuation, and investment horizon. Valuation-wise, if the market is trading significantly above historical averages, staggering the entry makes sense."""
    ),

    ("Long-Term Investing Principles", "Asset Allocation"): (
        IMG + "1611974789855-9c2a0a7236a3" + W,
        """Asset allocation is the strategic decision of how to divide your investment portfolio among different asset classes — equities, bonds (debt), gold, real estate, and cash. It is the single most important determinant of your portfolio's long-term risk and return. Research by Brinson, Hood, and Beebower famously found that asset allocation explains over 90% of the variation in portfolio returns — stock selection and market timing account for very little.

Different asset classes respond differently to economic conditions. Equities thrive in economic expansion but crash in recessions. Bonds typically do well when interest rates fall and when equities are weak — providing a diversification benefit. Gold tends to perform during currency crises, geopolitical uncertainty, and high inflation. Holding all three reduces portfolio volatility relative to holding only equities, even if it slightly reduces the expected return in a long bull market.

A classic rule of thumb is the "100 minus age" rule: the percentage of your portfolio in equities should equal 100 minus your age. A 30-year-old holds 70% equities; a 60-year-old holds 40%. This recognises that younger investors have more time to recover from crashes and can afford more volatility. Modern variants suggest "110 minus age" or "120 minus age" to account for longer lifespans and lower bond yields. Whatever formula you start with, adjust it to reflect your unique financial situation, risk tolerance, income stability, and investment goals."""
    ),

    ("Long-Term Investing Principles", "Rebalancing Your Portfolio"): (
        IMG + "1611974789855-9c2a0a7236a3" + W,
        """Rebalancing is the process of periodically returning your portfolio to its target asset allocation after market movements have caused drift. If you started with 60% equities and 40% debt, and equities surged to become 75% of your portfolio, rebalancing means selling some equities and buying debt to restore the 60/40 split. This may feel counterintuitive — why sell your best performers? — but it enforces a disciplined buy-low-sell-high discipline through systematic process.

The mechanics of rebalancing: first, decide on triggers — either calendar-based (rebalance every six months or once a year regardless of drift) or threshold-based (rebalance whenever any asset class drifts more than 5–10% from its target). Calendar-based is simpler; threshold-based may reduce unnecessary trading. When rebalancing, prefer to direct new contributions to underweight asset classes rather than selling overweight ones — this minimises transaction costs and tax triggers.

Rebalancing improves risk-adjusted returns over long periods by preventing your allocation from becoming dangerously concentrated in a single asset after a prolonged bull run. Many investors in 2000 who started with 60% equities ended up with 80–90% equities after the late 1990s tech boom — and suffered enormous losses in the subsequent crash. Had they rebalanced annually, they would have been selling equities at elevated valuations and buying bonds, emerging from the crash in much better condition."""
    ),

    ("Long-Term Investing Principles", "Tax-Efficient Investing"): (
        IMG + "1543286386-713bdd548da4" + W,
        """Taxes are one of the largest but most controllable costs of investing. Understanding how your gains are taxed — and structuring your portfolio to minimise unnecessary tax drag — can meaningfully increase your after-tax wealth over decades. In India, the key distinction for equity investments is the holding period: under one year yields Short-Term Capital Gains (STCG), taxed at 15%; over one year yields Long-Term Capital Gains (LTCG), taxed at 10% above ₹1 lakh exemption threshold.

This creates a powerful incentive to hold investments for at least one year. A ₹10 lakh gain after 364 days would attract ₹1.5 lakh in STCG tax; holding for 366 days, only about ₹90,000 in LTCG tax. The 5% difference in rate on ₹10 lakh = ₹50,000 in tax savings from one extra day of patience. For debt mutual funds, as of 2023, all capital gains (regardless of holding period) are taxed at your income tax slab rate — changing the calculus compared to pre-2023 rules.

Tax-loss harvesting — deliberately selling loss-making positions near year-end to offset gains — is a legitimate and widely practised technique. If you have realised ₹5 lakh in capital gains, selling a position with ₹3 lakh in unrealised losses to crystallise those losses reduces your taxable gain to ₹2 lakh. You can then immediately repurchase the same or equivalent assets if you still want exposure. ELSS (Equity Linked Saving Scheme) funds offer additional tax-saving benefits under Section 80C, making them a powerful component of a comprehensive tax-efficient portfolio strategy."""
    ),

    ("Long-Term Investing Principles", "Building a Core-Satellite Portfolio"): (
        IMG + "1579621970588-a35d0e7ab9b6" + W,
        """The core-satellite portfolio strategy combines the stability and cost-efficiency of passive index investing with the return potential of active stock selection or thematic bets. The "core" — typically 60–80% of the total portfolio — is invested in broad, low-cost index funds covering large-cap equity, total market, and perhaps international exposure. The core is designed to reliably capture market returns at minimal cost, ensuring the portfolio always participates in broad economic growth.

The "satellite" — the remaining 20–40% — is invested in higher-conviction, potentially higher-return strategies: individual stocks you have researched thoroughly, thematic funds (technology, healthcare, ESG), mid and small-cap active funds, or alternatives like gold. The satellite aims to generate "alpha" — returns above the market benchmark. Because the core is stable and well-diversified, satellite bets can be more aggressive without endangering the entire portfolio.

This structure has several advantages. Low core costs (index funds charge just 0.1–0.2% per year vs. 1–2% for active funds) save significant money over decades. The satellite keeps investing intellectually engaging and allows you to act on specific investment themes without risking your entire wealth on any single bet. And psychologically, having a structured framework prevents the emotional mistake of converting your entire portfolio into speculative bets during market euphoria."""
    ),

    ("Long-Term Investing Principles", "Summary & Key Takeaways"): (
        IMG + "1504711434969-e33886168f5c" + W,
        """Long-term investing is not complicated — but it is demanding in its requirement for patience, discipline, and systematic behaviour in the face of fear and greed. The principles could not be simpler: start early to maximise compounding,  invest regularly through SIPs, choose an appropriate asset allocation for your age and risk tolerance, rebalance periodically, minimise costs by favouring index funds, optimise for taxes by holding investments long enough to reach the LTCG threshold.

Compounding is the engine; time is the fuel; discipline is the driver. The most expensive investment mistakes are not bad stock picks — they are withdrawal of investments during market downturns, excessive trading that generates taxes and costs, over-concentration in a single stock or sector, and the paralysis of waiting for the "right time" to start investing. All of these are behavioural errors, not analytical ones.

Long-term investing is, at its core, a bet that economies grow, that human ingenuity creates value, and that productive businesses capture a share of that value and pass it to shareholders over time. This bet has paid off in every major economy over every long period in recorded history. It will require you to endure dramatic short-term losses without flinching — but for investors who can stay the course, the rewards compound to life-changing wealth."""
    ),

    # ── Module 8: Behavioural Finance & Psychology ────────────────
    ("Behavioural Finance & Psychology", "Why Psychology Matters in Investing"): (
        IMG + "1535320903710-d993d3d77d29" + W,
        """Classical economic theory assumes that investors are rational actors who process information objectively and always make decisions that maximise expected utility. Decades of research by psychologists Daniel Kahneman and Amos Tversky — for which Kahneman received the Nobel Prize in Economics in 2002 — proved this assumption fundamentally wrong. Real investors are driven by emotion, cognitive shortcuts, and systematic biases that cause them to make predictable, costly mistakes.

Behavioural finance is the field that bridges psychology and economics to explain why markets behave the way they do and why individual investors consistently underperform the markets they invest in. DALBAR's annual Quantitative Analysis of Investor Behaviour consistently finds that the average equity mutual fund investor earns 3–5% per year less than the funds they invest in — the difference explained almost entirely by behavioural errors: buying after rallies, selling after crashes, and constant fund-switching.

Understanding your own psychological vulnerabilities does not eliminate them — cognitive biases are hardwired into human neurology, not logical errors you can simply think your way out of. But awareness creates a pause between impulse and action. Every time you feel a powerful urge to sell everything, chase a hot stock, or follow a social media tip, recognising that urge as a potential bias rather than a rational signal gives you the chance to apply a rational check before acting. That pause is worth more than any stock-picking skill."""
    ),

    ("Behavioural Finance & Psychology", "Loss Aversion"): (
        IMG + "1611974789855-9c2a0a7236a3" + W,
        """Loss aversion is one of the most powerful and well-documented behavioural biases. Kahneman and Tversky's Prospect Theory found that the psychological pain of losing ₹1,000 is approximately twice as intense as the pleasure of gaining ₹1,000. This asymmetry causes investors to make irrational decisions designed to avoid the pain of realising a loss, even when those decisions make their financial situation worse.

The most direct expression of loss aversion is the reluctance to sell losing stocks. An investor who buys a stock at ₹100 and it falls to ₹60 refuses to sell — "I don't want to book the loss." But the loss has already occurred. Whether the stock is in your portfolio or the money is in your bank account at ₹60, the economic reality is identical. Refusing to sell a loser is often loss aversion masquerading as conviction. The right question is not "should I sell and book a loss?" but "if I had ₹60 in cash right now, would I choose to buy this stock?" If the answer is no, you should sell.

Loss aversion also causes investors to sell winners too early. Holding a winning position feels risky — the fear that the gain will evaporate grows stronger the larger the gain becomes. This "get-even-then-quit" mentality leads investors to systematically cut their winners short while letting their losers run — the precise opposite of the optimal strategy. The antidote is to evaluate every position on its future prospects, not its past performance relative to your purchase price."""
    ),

    ("Behavioural Finance & Psychology", "FOMO — Fear of Missing Out"): (
        IMG + "1590283603385-17ffb3a7f29f" + W,
        """FOMO — the Fear of Missing Out — is the anxiety that other investors are making money in a hot asset while you sit on the sidelines. In financial markets, it drives investors to chase rallies, buy assets at inflated valuations, and take on excessive risk — precisely when the risk-reward calculus is most unfavourable. FOMO is not new: it drove the tulip mania of 1637, the South Sea Bubble of 1720, the dot-com bubble of 1999, and every speculative excess since.

FOMO is particularly dangerous in the social media era. When your social circle is constantly sharing screenshots of 10x returns on crypto tokens, meme stocks, or IPO listings, the psychological pressure to participate becomes overwhelming. The human brain interprets exclusion from the group's activity as a social threat, triggering primal anxiety responses that hijack rational decision-making. Investment decisions made under FOMO rarely reflect genuine analysis of value — they reflect fear of social exclusion.

The practical defence against FOMO begins with having a written investment plan that specifies your strategy, criteria, and maximum allocation to speculative positions. When a hot new asset tempts you, check it against your plan. If it does not meet your criteria, the plan gives you permission — and rational justification — to stay on the sidelines. Remind yourself that you do not need to participate in every rally. Missing a 10x gain in a speculative asset is far better than participating in its subsequent 80% crash."""
    ),

    ("Behavioural Finance & Psychology", "Overconfidence Bias"): (
        IMG + "1454165804606-c3d57bc86b40" + W,
        """Overconfidence is the tendency to overestimate one's own abilities, knowledge, and the accuracy of one's forecasts. Studies consistently find that 80–90% of people rate themselves as above-average drivers — statistically impossible. In investing, overconfidence manifests as excessive trading (the belief that you can pick stocks or time markets better than you actually can), underestimation of risk (things only go wrong for other people), and overconcentration (too much money in one's "best ideas").

Terrance Odean and Brad Barber's landmark research on 78,000 household brokerage accounts found that investors who traded most frequently significantly underperformed the market — and that men traded 45% more than women and underperformed by 1.4% more per year. The irony: the more confident the investor, the worse the outcome on average, because higher conviction leads to higher trading activity, generating transaction costs and tax liabilities that drag returns.

Overconfidence is particularly dangerous in bull markets. When every stock you buy goes up (because the whole market is rising), it is natural to attribute those gains to skill rather than the macro environment. This inflated confidence leads to increasing position sizes and risk-taking just as the market approaches a peak. The remedy: track every investment decision in a journal, including your reasoning and prediction. Review it honestly after 12 months. Most investors find their actual track record is far more humbling than their remembered track record."""
    ),

    ("Behavioural Finance & Psychology", "Herd Mentality"): (
        IMG + "1579621970588-a35d0e7ab9b6" + W,
        """Herd mentality — the tendency to follow what the crowd is doing — is an evolutionary survival instinct that becomes financially destructive in investment markets. In prehistoric times, following the group's behaviour (fleeing when others fled, eating when others ate) was often the rational survival strategy. In financial markets, however, the crowd is frequently wrong at extremes: it is most bullish at market tops and most bearish at market bottoms — the exact opposite of when you should be optimistic or pessimistic.

The mechanics of herding in markets: as an asset rises, more media coverage attracts more investors, who drive the price higher, generating more media coverage — a feedback loop that can push prices far above rational valuations. When the herd eventually loses confidence and begins to exit, the same feedback loop works in reverse, driving prices far below fundamental value. Both the 2008 financial crisis and the 2020 COVID crash are examples of herd-driven price dislocations that ultimately corrected sharply.

Contrarian investing — deliberately doing the opposite of what the crowd is doing — is the most consistent way to benefit from herding. This does not mean contrarianism for its own sake, or stubbornly holding losing positions because everyone else has sold. It means maintaining the courage and analytical discipline to buy high-quality assets when sentiment is at its worst (and prices reflect maximum pessimism) and to sell or reduce exposure when everyone is euphoric and prices reflect maximum optimism."""
    ),

    ("Behavioural Finance & Psychology", "Anchoring Bias"): (
        IMG + "1551288049-bebda4e38f71" + W,
        """Anchoring is the cognitive bias of placing excessive weight on the first piece of information encountered when making decisions. In investing, the most common anchor is the price at which you purchased an investment. If you bought a stock at ₹500 and it has fallen to ₹300, you may think "it's cheap now — it was ₹500 just six months ago." But your purchase price is irrelevant to whether ₹300 is a good current value. The market does not know what you paid; it does not care.

Other common investment anchors: the 52-week high (investors anchor to a stock's recent peak and assume a decline from that high represents a bargain, regardless of fundamentals). Analyst price targets (the first target you hear creates an implicit expectation that distorts how you process subsequent information). IPO prices (investors anchor to the IPO price and resist buying above it, even when the business has grown substantially since listing).

The corrective practice is to evaluate every investment purely on its current price relative to its intrinsic value — an analysis that explicitly ignores your historical cost or any other anchoring number. Ask: "If I had no position in this stock and only had today's information, would I buy it at today's price?" If the answer is "no, but I'm hanging on because I paid more," that is anchoring, not investing. Separating your entry price from your appraisal of the business is one of the most liberating disciplines in value investing."""
    ),

    ("Behavioural Finance & Psychology", "Emotional Discipline"): (
        IMG + "1568515387631-8b650bbcdb90" + W,
        """Emotional discipline — the ability to follow your investment plan consistently, especially when it is emotionally most difficult — is the ultimate investing skill. Knowledge of financial statements, valuation methods, and technical indicators is worthless if you panic and sell at the bottom or abandon your strategy during a drawdown. The investor who earns the highest long-term return is not the most brilliant analyst — it is the most disciplined and patient participant.

Building emotional discipline requires systems, not willpower. Willpower is exhaustible and fails precisely when it is needed most (during market extremes). Systems are automatic and consistent. The most effective system is a written Investment Policy Statement (IPS): a personal document that specifies your goals, time horizon, asset allocation, rebalancing rules, criteria for buying and selling specific investments, and the maximum allocation to speculative bets. When emotions urge you to deviate, the IPS provides a rational anchor.

Trade journaling is a powerful complementary practice. For every investment decision — buy, hold, or sell — write down your reasoning, the key facts supporting your view, and what would change your mind. Review past entries regularly. Over time, patterns will emerge: are you consistently making buying decisions after rallies? Selling during drawdowns? Over-weighting speculative tips? Identifying your personal pattern of errors is the first step to overriding them. Most successful investors describe their journey as learning, slowly and painfully, to get out of their own way."""
    ),

    ("Behavioural Finance & Psychology", "Summary & Key Takeaways"): (
        IMG + "1504711434969-e33886168f5c" + W,
        """Behavioural finance shows us that investment success is more a psychological achievement than an intellectual one. The same market data is available to everyone; what separates great investors from poor ones is not access to better information but the ability to act rationally when instinct, social pressure, and emotion are screaming otherwise.

You have now studied the major biases: loss aversion (feeling losses twice as intensely as gains), FOMO (chasing rallies out of social anxiety), overconfidence (trading too much based on inflated self-assessment), herding (following the crowd into boom-and-bust cycles), and anchoring (over-weighting irrelevant reference prices). Each of these biases has a known antidote: a written plan, systematic rules, journaling, and regular honest performance review.

The journey of self-improvement as an investor never fully ends — no one eliminates their biases entirely. But each bias you identify and develop a systematic response to removes one more source of expensive error. Combine this psychological awareness with the fundamental and technical knowledge from earlier modules, and you will possess a remarkably powerful toolkit for building long-term wealth. Now go take the quiz — calm, rational, and clear-eyed."""
    ),
})
