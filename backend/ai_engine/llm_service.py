import os
import time
import traceback

from google import genai

from trading.models import Wallet, Holding, TradeLog, Stock
from .models import AIInsight


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_client():
    api_key = os.getenv("GEMINI_API_KEY")
    print("GEMINI API KEY PRESENT:", bool(api_key))
    return genai.Client(api_key=api_key)


def get_model_name():
    m = os.getenv("GEMINI_MODEL", "gemini-3-flash-preview")
    print("USING GEMINI MODEL:", m)
    return m


def clean_text(x):
    if not x:
        return ""
    x = x.replace("**", "")
    x = x.replace("__", "")
    x = x.replace("–", "-")
    return x.strip()


def safe_float(x, d=0.0):
    try:
        if x is None:
            return d
        return float(x)
    except (TypeError, ValueError):
        return d


def safe_str(x, d=""):
    if x is None:
        return d
    return str(x)


def is_greeting(msg):
    m = (msg or "").lower().strip()
    gs = {
        "hi", "hello", "hey", "hii", "heyy", "yo",
        "good morning", "good afternoon", "good evening"
    }
    return m in gs


def load_static_context():
    try:
        path = os.path.join(BASE_DIR, "ai_engine", "app_context.txt")
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print("STATIC CONTEXT LOAD ERROR:", repr(e))
        return ""


def get_fallback_reply(user_message, reason="unknown"):
    print(f"USING FALLBACK: {reason}")

    msg = (user_message or "").lower().strip()

    if is_greeting(msg):
        return "Hi! How can I help you today?"

    return "Sorry, I could not generate a response right now. Please try again in a short while."


def get_wallet_text(user):
    try:
        wallet = Wallet.objects.filter(student=user).first()
        if not wallet:
            return "No wallet found."
        return f"Wallet balance: {round(safe_float(wallet.balance), 2)} {safe_str(getattr(wallet, 'currency', 'INR'), 'INR')}"
    except Exception as e:
        print("WALLET READ ERROR:", repr(e))
        return "Wallet data unavailable."


def get_holdings_text(user, limit=15):
    try:
        qs = (
            Holding.objects
            .filter(student=user)
            .select_related("stock")
            .order_by("-quantity")[:limit]
        )

        if not qs.exists():
            return "No holdings found."

        lines = []
        total_cost = 0.0
        total_current = 0.0

        for h in qs:
            sym = safe_str(getattr(h.stock, "symbol", "Unknown"))
            qty = safe_float(getattr(h, "quantity", 0))
            avg_buy = safe_float(getattr(h, "avg_buy_price", 0))
            cur = safe_float(getattr(h.stock, "current_price", 0))
            invested = qty * avg_buy
            current = qty * cur
            pnl = current - invested

            total_cost += invested
            total_current += current

            lines.append(
                f"{sym}: qty={qty}, avg_buy={round(avg_buy,2)}, current_price={round(cur,2)}, current_value={round(current,2)}, pnl={round(pnl,2)}"
            )

        out = [
            f"Holdings count: {qs.count()}",
            f"Total invested amount: {round(total_cost, 2)}",
            f"Total current holding value: {round(total_current, 2)}",
            "Holdings detail:"
        ]
        out.extend(lines)
        return "\n".join(out)

    except Exception as e:
        print("HOLDINGS READ ERROR:", repr(e))
        return "Holdings data unavailable."


def get_recent_trades_text(user, limit=10):
    try:
        qs = TradeLog.objects.filter(student=user).order_by("-executed_at")[:limit]

        if not qs.exists():
            return "No recent trades found."

        lines = []
        buy_ct = 0
        sell_ct = 0
        total_buy_value = 0.0
        total_sell_value = 0.0

        for t in qs:
            sym = safe_str(getattr(t, "stock_symbol", "Unknown"))
            typ = safe_str(getattr(t, "order_type", "Unknown"))
            qty = safe_float(getattr(t, "quantity", 0))
            price = safe_float(getattr(t, "price", 0))
            total_value = safe_float(getattr(t, "total_value", 0))
            wb = safe_float(getattr(t, "wallet_balance_before", 0))
            wa = safe_float(getattr(t, "wallet_balance_after", 0))
            tm = getattr(t, "executed_at", None)

            if typ.upper() == "BUY":
                buy_ct += 1
                total_buy_value += total_value
            elif typ.upper() == "SELL":
                sell_ct += 1
                total_sell_value += total_value

            lines.append(
                f"{typ} {qty} of {sym} at {round(price,2)} for value {round(total_value,2)}; wallet before={round(wb,2)}, wallet after={round(wa,2)}, time={tm}"
            )

        out = [
            f"Recent trade count: {qs.count()}",
            f"Recent buys: {buy_ct}",
            f"Recent sells: {sell_ct}",
            f"Recent buy value: {round(total_buy_value,2)}",
            f"Recent sell value: {round(total_sell_value,2)}",
            "Recent trade detail:"
        ]
        out.extend(lines)
        return "\n".join(out)

    except Exception as e:
        print("TRADES READ ERROR:", repr(e))
        return "Trade history unavailable."


def get_latest_ai_insight_text(user):
    try:
        x = AIInsight.objects.filter(user=user).order_by("-created_at").first()
        if not x:
            return "No previous AI insight found."

        return "\n".join([
            "Latest saved AI insight:",
            f"Risk profile: {safe_str(getattr(x, 'risk_profile', ''))}",
            f"Trader type: {safe_str(getattr(x, 'trader_type', ''))}",
            f"Anomaly detected: {safe_str(getattr(x, 'anomaly_detected', False))}",
            f"Anomaly score: {safe_float(getattr(x, 'anomaly_score', 0))}",
            f"Summary: {safe_str(getattr(x, 'summary', ''))}",
        ])
    except Exception as e:
        print("AI INSIGHT READ ERROR:", repr(e))
        return "AI insight data unavailable."


def get_available_stocks_text(limit=200):
    try:
        qs = Stock.objects.all().order_by("symbol")[:limit]
        if not qs.exists():
            return "No stocks are currently available on the platform."

        arr = []
        for s in qs:
            sym = safe_str(getattr(s, "symbol", "Unknown"))
            name = safe_str(getattr(s, "company_name", ""))
            sector = safe_str(getattr(s, "sector", ""))
            price = safe_float(getattr(s, "current_price", 0))

            line = sym
            if name:
                line += f" - {name}"
            if sector:
                line += f" - sector: {sector}"
            line += f" - current price: {round(price,2)}"
            arr.append(line)

        return "Stocks available on the app:\n" + "\n".join(arr)

    except Exception as e:
        print("STOCK LIST READ ERROR:", repr(e))
        return "Stock universe unavailable."


def get_rule_based_text(rule_based):
    if not rule_based:
        return "No rule-based analysis found."

    parts = ["Rule-based analysis:"]
    parts.append(f"Trade count last 7 days: {rule_based.get('trade_count_last_7_days', 'N/A')}")
    parts.append(f"Wallet balance: {rule_based.get('wallet_balance', 'N/A')}")
    parts.append(f"Portfolio concentration: {rule_based.get('portfolio_concentration', 'N/A')}")
    parts.append(f"Risk profile: {rule_based.get('risk_profile', 'N/A')}")

    tips = rule_based.get("tips", [])
    if tips:
        parts.append("Rule-based tips:")
        for t in tips:
            parts.append(f"- {t}")

    return "\n".join(parts)


def get_ml_based_text(ml_based):
    if not ml_based:
        return "No ML analysis found."

    parts = ["ML-based analysis:"]
    parts.append(f"ML available: {ml_based.get('ml_available', False)}")
    parts.append(f"Trader type: {ml_based.get('trader_type', 'N/A')}")
    parts.append(f"Anomaly detected: {ml_based.get('is_anomaly', False)}")
    parts.append(f"Anomaly score: {ml_based.get('anomaly_score', 'N/A')}")
    return "\n".join(parts)


def get_final_tips_text(final_tips):
    if not final_tips:
        return "No final tips found."

    parts = ["Final combined tips:"]
    for t in final_tips:
        parts.append(f"- {t}")
    return "\n".join(parts)


def build_user_context(context):
    user = context.get("user")
    username = safe_str(context.get("username", ""))

    parts = []

    if username:
        parts.append(f"Username: {username}")

    if user is not None:
        parts.append(get_wallet_text(user))
        parts.append(get_holdings_text(user))
        parts.append(get_recent_trades_text(user))
        parts.append(get_latest_ai_insight_text(user))

    rule_based = context.get("rule_based")
    ml_based = context.get("ml_based")
    final_tips = context.get("final_tips")

    if rule_based:
        parts.append(get_rule_based_text(rule_based))

    if ml_based:
        parts.append(get_ml_based_text(ml_based))

    if final_tips:
        parts.append(get_final_tips_text(final_tips))

    return "\n\n".join(parts)


def call_gemini(client, contents, max_retries=2):
    last_err = None

    for i in range(max_retries + 1):
        try:
            return client.models.generate_content(
                model=get_model_name(),
                contents=contents,
            )
        except Exception as e:
            last_err = e
            s = str(e)
            print("GEMINI CALL ERROR:", repr(e))

            if "429" in s or "RESOURCE_EXHAUSTED" in s:
                wait_s = 10 * (i + 1)
                print(f"Rate limit hit. Sleeping for {wait_s}s")
                time.sleep(wait_s)
                continue

            raise e

    raise last_err


def get_chatbot_reply(context):
    user_message = safe_str(context.get("user_message", "")).strip()

    if not user_message:
        return "Please ask something."

    if is_greeting(user_message):
        return "Hi! How can I help you with trading or anything else today?"

    static_context = load_static_context()
    user_context = build_user_context(context)
    available_stocks_text = get_available_stocks_text()

    system_prompt = """
You are an AI assistant inside a financial trading and learning platform.

You will receive:
- Platform knowledge
- User-specific platform data
- Available platform stocks
- The user's question

Follow these rules carefully:
- Answer only the user's actual question.
- Use platform knowledge whenever relevant.
- User-specific data is secondary context.
- Use user-specific data only when the question is specifically about the user's own portfolio, wallet, holdings, trades, account activity, risk, or asks for a personal recommendation.
- If the question is general, conceptual, educational, or about broad market or world scenarios, do not mention the user's personal data unless the user explicitly asks to relate the answer to their own situation.
- Use the available platform stocks only when they are relevant to the question.
- Never say you do not have access to the user data if it is provided below.
- Never ask for wallet, holdings, or trade details if they are already provided below.
- Do not invent facts, values, holdings, stocks, prices, or app features.
- If some relevant detail is missing, briefly say what is missing.
- Do not promise profits or certainty.
- Keep the answer in simple English.
- Use plain text only.
- Be clear, direct, and useful.
- Keep the answer moderately detailed unless the user asks for a shorter one.
""".strip()

    try:
        client = get_client()

        blocks = []

        if static_context:
            blocks.append("PLATFORM KNOWLEDGE:\n" + static_context)

        if available_stocks_text:
            blocks.append(
                "AVAILABLE PLATFORM STOCKS:\n"
                + available_stocks_text
            )

        if user_context:
            blocks.append(
                "USER-SPECIFIC PLATFORM DATA:\n"
                + user_context
            )

        blocks.append("USER QUESTION:\n" + user_message)

        full_input = "\n\n".join(blocks)

        response = call_gemini(
            client,
            [
                system_prompt,
                full_input
            ],
            max_retries=2
        )

        print("RAW GEMINI RESPONSE:", response)

        text = clean_text(getattr(response, "text", ""))

        if text:
            print("LLM SUCCESS: Gemini returned text")
            return text

        return get_fallback_reply(user_message, "empty Gemini text")

    except Exception as e:
        print("GEMINI ERROR:", repr(e))
        traceback.print_exc()
        return get_fallback_reply(user_message, f"exception: {repr(e)}")