from decimal import Decimal
from django.db.models import Avg, Count, Sum, Q
from trading.models import TradeLog, Wallet, Holding


def to_f(x, d=0.0):
    try:
        if x is None:
            return d
        return float(x)
    except:
        return d


def r2(x):
    return round(to_f(x), 2)


def get_user_trade_stats(user):
    qs = TradeLog.objects.filter(student=user)

    total_trades = qs.count()

    avg_trade_size = qs.aggregate(v=Avg("total_value"))["v"] or Decimal("0")
    total_trade_value = qs.aggregate(v=Sum("total_value"))["v"] or Decimal("0")

    buy_count = qs.filter(order_type="BUY").count()
    sell_count = qs.filter(order_type="SELL").count()

    last_wallet = (
        qs.order_by("-executed_at")
        .values_list("wallet_balance_after", flat=True)
        .first()
    )

    if last_wallet is None:
        w = Wallet.objects.filter(student=user).first()
        last_wallet = w.balance if w else Decimal("0")

    return {
        "total_trades": total_trades,
        "avg_trade_size": r2(avg_trade_size),
        "total_trade_value": r2(total_trade_value),
        "buy_count": buy_count,
        "sell_count": sell_count,
        "wallet_balance": r2(last_wallet),
    }


def get_user_holding_stats(user):
    qs = Holding.objects.filter(student=user)

    total_positions = qs.count()

    total_qty = qs.aggregate(v=Sum("quantity"))["v"] or 0

    total_cost = Decimal("0")
    mx = Decimal("0")

    for h in qs:
        v = Decimal(h.quantity) * h.avg_buy_price
        total_cost += v
        if v > mx:
            mx = v

    concentration = 0.0
    if total_cost > 0:
        concentration = float(mx / total_cost) * 100.0

    return {
        "portfolio_diversity": total_positions,
        "total_quantity": int(total_qty),
        "portfolio_cost_basis": r2(total_cost),
        "portfolio_concentration_pct": round(concentration, 2),
    }


def get_all_user_ids():
    ids1 = list(TradeLog.objects.values_list("student_id", flat=True).distinct())
    ids2 = list(Holding.objects.values_list("student_id", flat=True).distinct())
    ids3 = list(Wallet.objects.values_list("student_id", flat=True).distinct())
    return list(set(ids1 + ids2 + ids3))


def get_peer_baseline():
    user_ids = get_all_user_ids()
    n = len(user_ids)

    if n == 0:
        return {
            "peer_user_count": 0,
            "avg_total_trades": 0.0,
            "avg_trade_size": 0.0,
            "avg_wallet_balance": 0.0,
            "avg_portfolio_diversity": 0.0,
            "avg_portfolio_concentration_pct": 0.0,
        }

    trade_rows = (
        TradeLog.objects.values("student")
        .annotate(
            total_trades=Count("id"),
            avg_trade_size=Avg("total_value"),
            buy_count=Count("id", filter=Q(order_type="BUY")),
            sell_count=Count("id", filter=Q(order_type="SELL")),
        )
    )

    hold_rows = (
        Holding.objects.values("student")
        .annotate(
            portfolio_diversity=Count("stock", distinct=True),
        )
    )

    wallet_rows = Wallet.objects.values("student", "balance")

    trade_map = {
        row["student"]: {
            "total_trades": row["total_trades"] or 0,
            "avg_trade_size": to_f(row["avg_trade_size"]),
        }
        for row in trade_rows
    }

    hold_map = {
        row["student"]: {
            "portfolio_diversity": row["portfolio_diversity"] or 0,
        }
        for row in hold_rows
    }

    wallet_map = {
        row["student"]: to_f(row["balance"])
        for row in wallet_rows
    }

    s_tr = 0.0
    s_avg = 0.0
    s_w = 0.0
    s_div = 0.0
    s_conc = 0.0

    for uid in user_ids:
        s_tr += trade_map.get(uid, {}).get("total_trades", 0)
        s_avg += trade_map.get(uid, {}).get("avg_trade_size", 0.0)
        s_w += wallet_map.get(uid, 0.0)
        s_div += hold_map.get(uid, {}).get("portfolio_diversity", 0)

        user_holdings = Holding.objects.filter(student_id=uid)
        total_cost = Decimal("0")
        mx = Decimal("0")

        for h in user_holdings:
            v = Decimal(h.quantity) * h.avg_buy_price
            total_cost += v
            if v > mx:
                mx = v

        c = 0.0
        if total_cost > 0:
            c = float(mx / total_cost) * 100.0

        s_conc += c

    return {
        "peer_user_count": n,
        "avg_total_trades": round(s_tr / n, 2),
        "avg_trade_size": round(s_avg / n, 2),
        "avg_wallet_balance": round(s_w / n, 2),
        "avg_portfolio_diversity": round(s_div / n, 2),
        "avg_portfolio_concentration_pct": round(s_conc / n, 2),
    }


def compare_label(x, y, tol=0.1):
    if y == 0:
        if x == 0:
            return "about the same"
        return "higher"
    d = (x - y) / y
    if d > tol:
        return "higher"
    if d < -tol:
        return "lower"
    return "about the same"


def build_comparison_text(us, ps):
    out = []

    a = compare_label(us["total_trades"], ps["avg_total_trades"])
    out.append(f"Trade frequency is {a} than peer average.")

    a = compare_label(us["avg_trade_size"], ps["avg_trade_size"])
    out.append(f"Average trade size is {a} than peer average.")

    a = compare_label(us["wallet_balance"], ps["avg_wallet_balance"])
    out.append(f"Wallet balance is {a} than peer average.")

    a = compare_label(us["portfolio_diversity"], ps["avg_portfolio_diversity"])
    out.append(f"Portfolio diversification is {a} than peer average.")

    a = compare_label(
        us["portfolio_concentration_pct"],
        ps["avg_portfolio_concentration_pct"]
    )
    out.append(f"Portfolio concentration is {a} than peer average.")

    return out


def get_peer_summary(user, risk_profile=None, trader_type=None):
    user_trade = get_user_trade_stats(user)
    user_hold = get_user_holding_stats(user)

    user_stats = {}
    user_stats.update(user_trade)
    user_stats.update(user_hold)

    peer_base = get_peer_baseline()

    comparison_points = build_comparison_text(user_stats, peer_base)

    tips = []

    if user_stats["total_trades"] > peer_base["avg_total_trades"]:
        tips.append("Your trading frequency is above average, so reducing unnecessary trades may improve stability.")

    if user_stats["avg_trade_size"] > peer_base["avg_trade_size"]:
        tips.append("Your average trade size is above peer average, so smaller position sizes may reduce risk.")

    if user_stats["portfolio_diversity"] < peer_base["avg_portfolio_diversity"]:
        tips.append("Your portfolio is less diversified than average, so spreading capital across more stocks may help.")

    if user_stats["portfolio_concentration_pct"] > peer_base["avg_portfolio_concentration_pct"]:
        tips.append("A large share of your portfolio is concentrated in one position, so reducing concentration may improve balance.")

    if not tips:
        tips.append("Your trading pattern is reasonably close to peer averages. Focus on consistency and disciplined position sizing.")

    return {
        "user_stats": user_stats,
        "peer_summary": peer_base,
        "comparison_points": comparison_points,
        "peer_generated_tips": tips,
    }