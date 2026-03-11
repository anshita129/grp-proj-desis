import pandas as pd
import numpy as np

np.random.seed(42)

symbols = ["AAPL", "MSFT", "TSLA", "GOOG"]

rows_per_symbol = 50000   # total rows = 250k

start_prices = {
    "AAPL":150,
    "MSFT":300,
    "TSLA":220,
    "GOOG":130
}

data = []

for sym in symbols:
    price = start_prices[sym]

    timestamps = pd.date_range(
        start="2024-01-01",
        periods=rows_per_symbol,
        freq="1min"
    )

    for ts in timestamps:

        change = np.random.normal(0,0.5)

        open_price = price
        close_price = max(1, open_price + change)

        high = max(open_price, close_price) + abs(np.random.normal(0,0.3))
        low = min(open_price, close_price) - abs(np.random.normal(0,0.3))

        volume = int(abs(np.random.normal(6000,2000)))

        data.append([
            sym,
            ts,
            round(open_price,2),
            round(high,2),
            round(low,2),
            round(close_price,2),
            volume
        ])

        price = close_price

df = pd.DataFrame(
    data,
    columns=["symbol","timestamp","open","high","low","close","volume"]
)

df.to_csv("market_simulation_data2.csv", index=False)

print("Dataset saved as market_simulation_data.csv")