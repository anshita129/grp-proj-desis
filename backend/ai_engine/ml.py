import os
import joblib
import pandas as pd

from django.conf import settings
from django.contrib.auth import get_user_model
from sklearn.cluster import KMeans
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from trading.models import TradeLog
from portfolio.models import Holding


MODEL_DIR = os.path.join(settings.BASE_DIR, "ai_engine", "saved_models")
SCALER_PATH = os.path.join(MODEL_DIR, "scaler.joblib")
KMEANS_PATH = os.path.join(MODEL_DIR, "kmeans.joblib")
ISO_PATH = os.path.join(MODEL_DIR, "isolation_forest.joblib")

FEATURE_COLUMNS = [
    "trade_count",
    "buy_count",
    "sell_count",
    "total_trade_value",
    "avg_trade_value",
    "wallet_balance",
    "portfolio_value",
    "portfolio_concentration",
    "unique_assets",
]


def ensure_model_dir():
    os.makedirs(MODEL_DIR, exist_ok=True)


def safe_float(x, default=0.0):
    try:
        if x is None:
            return default
        return float(x)
    except (TypeError, ValueError):
        return default


def get_latest_wallet_balance(user):
    last_trade = TradeLog.objects.filter(student=user).order_by("-executed_at").first()
    if not last_trade:
        return 0.0
    return safe_float(getattr(last_trade, "wallet_balance_after", 0.0))


def get_user_features(user):
    trades = TradeLog.objects.filter(student=user)
    holdings = Holding.objects.filter(user=user)

    trade_count = trades.count()
    buy_count = trades.filter(order_type__iexact="BUY").count()
    sell_count = trades.filter(order_type__iexact="SELL").count()

    total_trade_value = 0.0
    for t in trades:
        total_trade_value += safe_float(getattr(t, "total_value", 0.0))

    avg_trade_value = total_trade_value / trade_count if trade_count > 0 else 0.0
    wallet_balance = get_latest_wallet_balance(user)

    portfolio_value = 0.0
    max_holding_value = 0.0
    unique_assets = holdings.count()

    for h in holdings:
        qty = safe_float(getattr(h, "quantity", 0.0))
        avg_buy_price = safe_float(getattr(h, "avg_buy_price", 0.0))
        value = qty * avg_buy_price
        portfolio_value += value
        if value > max_holding_value:
            max_holding_value = value

    portfolio_concentration = (
        max_holding_value / portfolio_value if portfolio_value > 0 else 0.0
    )

    return {
        "trade_count": trade_count,
        "buy_count": buy_count,
        "sell_count": sell_count,
        "total_trade_value": total_trade_value,
        "avg_trade_value": avg_trade_value,
        "wallet_balance": wallet_balance,
        "portfolio_value": portfolio_value,
        "portfolio_concentration": portfolio_concentration,
        "unique_assets": unique_assets,
    }


def get_training_dataframe():
    User = get_user_model()
    users = User.objects.all()

    rows = []
    for user in users:
        rows.append(get_user_features(user))

    if not rows:
        return pd.DataFrame()

    return pd.DataFrame(rows)


def train_models(df):
    if df.empty:
        raise ValueError("No user data found for training.")

    if len(df) < 10:
        raise ValueError("At least 10 users are recommended for ML training.")

    X = df[FEATURE_COLUMNS].fillna(0.0)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    n_clusters = min(3, len(df))
    if n_clusters < 2:
        raise ValueError("Need at least 2 users to form clusters.")

    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    kmeans.fit(X_scaled)

    iso = IsolationForest(
        n_estimators=100,
        contamination=0.1,
        random_state=42
    )
    iso.fit(X_scaled)

    ensure_model_dir()
    joblib.dump(scaler, SCALER_PATH)
    joblib.dump(kmeans, KMEANS_PATH)
    joblib.dump(iso, ISO_PATH)

    return {
        "trained_users": len(df),
        "n_clusters": n_clusters,
    }


def models_exist():
    return (
        os.path.exists(SCALER_PATH)
        and os.path.exists(KMEANS_PATH)
        and os.path.exists(ISO_PATH)
    )


def load_models():
    if not models_exist():
        return None

    try:
        scaler = joblib.load(SCALER_PATH)
        kmeans = joblib.load(KMEANS_PATH)
        iso = joblib.load(ISO_PATH)
    except Exception:
        return None

    return {
        "scaler": scaler,
        "kmeans": kmeans,
        "isolation_forest": iso,
    }


def interpret_trader_type(cluster_label, features):
    tc = features["trade_count"]
    pc = features["portfolio_concentration"]
    ua = features["unique_assets"]
    atv = features["avg_trade_value"]

    if tc >= 20 and pc >= 0.6:
        return "High Activity Concentrated Trader"
    if tc >= 20:
        return "Active Trader"
    if pc >= 0.6 and ua <= 2:
        return "Concentrated Investor"
    if atv < 1000 and tc < 10:
        return "Small Volume Cautious Trader"
    return f"Behavior Cluster {cluster_label}"


def predict_user_behavior(user):
    models = load_models()
    if not models:
        return {
            "ml_available": False,
            "reason": "Models are not trained or could not be loaded."
        }

    try:
        features = get_user_features(user)
        X = pd.DataFrame([features])[FEATURE_COLUMNS].fillna(0.0)
        X_scaled = models["scaler"].transform(X)

        cluster_label = int(models["kmeans"].predict(X_scaled)[0])
        anomaly_raw = int(models["isolation_forest"].predict(X_scaled)[0])
        anomaly_score = float(models["isolation_forest"].decision_function(X_scaled)[0])

        trader_type = interpret_trader_type(cluster_label, features)
        is_anomaly = anomaly_raw == -1

        return {
            "ml_available": True,
            "features": features,
            "cluster_label": cluster_label,
            "trader_type": trader_type,
            "is_anomaly": is_anomaly,
            "anomaly_score": anomaly_score,
        }

    except Exception as e:
        return {
            "ml_available": False,
            "reason": f"Prediction failed: {str(e)}"
        }