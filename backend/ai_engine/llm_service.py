import os
import time
import traceback

from google import genai

from trading.models import Wallet, Holding, TradeLog, Stock
from .models import AIInsight
from learning.models import LessonProgress, QuizAttempt, UserBadge
from dotenv import load_dotenv


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

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

def get_learning_text(user, lesson_limit=10, quiz_limit=5, badge_limit=5):
    try:
        lesson_qs = (
            LessonProgress.objects
            .filter(user=user)
            .select_related("lesson", "lesson__module")
            .order_by("-completed_at")[:lesson_limit]
        )

        quiz_qs = (
            QuizAttempt.objects
            .filter(user=user)
            .select_related("quiz", "quiz__module")
            .order_by("-attempted_at")[:quiz_limit]
        )

        badge_qs = (
            UserBadge.objects
            .filter(user=user)
            .select_related("badge")
            .order_by("-awarded_at")[:badge_limit]
        )

        total_completed_lessons = LessonProgress.objects.filter(user=user).count()
        total_quiz_attempts = QuizAttempt.objects.filter(user=user).count()
        passed_quizzes = QuizAttempt.objects.filter(user=user, passed=True).count()

        parts = ["Learning data:"]

        if total_completed_lessons == 0 and total_quiz_attempts == 0 and not badge_qs.exists():
            return "Learning data: No learning progress found."

        parts.append(f"Completed lessons: {total_completed_lessons}")
        parts.append(f"Quiz attempts: {total_quiz_attempts}")
        parts.append(f"Passed quizzes: {passed_quizzes}")

        if quiz_qs.exists():
            avg_score_raw = 0.0
            avg_pct_raw = 0.0
            cnt = 0

            parts.append("Recent quiz attempts:")
            for q in quiz_qs:
                module_title = q.quiz.module.title if q.quiz and q.quiz.module else "Unknown module"
                quiz_title = q.quiz.title if q.quiz else "Unknown quiz"
                score = safe_float(q.score)
                total = max(1, safe_float(q.total_questions, 1))
                pct = round((score / total) * 100.0, 2)

                avg_score_raw += score
                avg_pct_raw += pct
                cnt += 1

                status = "Passed" if q.passed else "Failed"
                parts.append(
                    f"- Module: {module_title}, Quiz: {quiz_title}, Score: {int(score)}/{int(total)}, Percentage: {pct}%, Result: {status}"
                )

            parts.append(f"Average recent quiz percentage: {round(avg_pct_raw / cnt, 2)}%")

        if lesson_qs.exists():
            parts.append("Recently completed lessons:")
            seen_modules = set()

            for lp in lesson_qs:
                lesson_title = lp.lesson.title if lp.lesson else "Unknown lesson"
                module_title = lp.lesson.module.title if lp.lesson and lp.lesson.module else "Unknown module"
                difficulty = lp.lesson.module.difficulty if lp.lesson and lp.lesson.module else "Unknown"
                seen_modules.add((module_title, difficulty))

                parts.append(
                    f"- Module: {module_title}, Difficulty: {difficulty}, Lesson: {lesson_title}"
                )

            if seen_modules:
                parts.append("Modules covered recently:")
                for module_title, difficulty in list(seen_modules)[:5]:
                    parts.append(f"- {module_title} ({difficulty})")

        if badge_qs.exists():
            parts.append("Earned badges:")
            for ub in badge_qs:
                badge_name = ub.badge.name if ub.badge else "Unknown badge"
                badge_desc = ub.badge.description if ub.badge else ""
                reward = ub.badge.reward_amount if ub.badge else 0
                parts.append(
                    f"- Badge: {badge_name}, Reward: {reward}, Description: {badge_desc}"
                )

        weak_modules = []
        for q in quiz_qs:
            total = max(1, safe_float(q.total_questions, 1))
            pct = (safe_float(q.score) / total) * 100.0
            if pct < 50:
                module_title = q.quiz.module.title if q.quiz and q.quiz.module else "Unknown module"
                weak_modules.append(module_title)

        if weak_modules:
            parts.append("Possible weak areas based on recent quiz scores:")
            for x in list(dict.fromkeys(weak_modules))[:5]:
                parts.append(f"- {x}")

        return "\n".join(parts)

    except Exception as e:
        print("LEARNING DATA READ ERROR:", repr(e))
        return "Learning data unavailable."

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
        parts.append(get_learning_text(user))
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
- Use user-specific data only when the question is specifically about the user's own portfolio, wallet, holdings, trades, account activity, learning progress, quiz performance, badges, risk, or asks for a personal recommendation.
- If learning progress is available, use it to adjust the explanation level and recommend relevant concepts or lessons when helpful.
- If the question is general or conceptual, do not unnecessarily mention private user data.
- Never invent facts, scores, holdings, lesson completion, or platform features.
- If some relevant detail is missing, briefly say so.
- Do not promise profits or certainty.
- Keep the answer in simple English.
- Use plain text only.
- Be clear, direct, and useful.
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