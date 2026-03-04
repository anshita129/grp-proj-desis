"""CSV-backed price store for local ingestion.

Fulfills the constraint that historical data must be stored locally
and ingested easily without tying to a live database.
"""
import csv
from datetime import date, datetime
from typing import Dict, Iterable, List, Optional, Set
from pathlib import Path

from market_simulation.replay.price_store import PriceStore, OHLC

class CSVPriceStore(PriceStore):
    """Loads historical OHLC data from a local CSV file.
    
    Expected CSV columns: Date, Symbol, Open, High, Low, Close, Volume
    Date format expected: YYYY-MM-DD
    """
    def __init__(self, filepath: Path) -> None:
        self.filepath = Path(filepath)
        self._prices: Dict[date, Dict[str, OHLC]] = {}
        self._days_sorted: List[date] = []
        self._load_csv()

    def _load_csv(self) -> None:
        if not self.filepath.exists():
            raise FileNotFoundError(f"CSV file not found at {self.filepath}")

        with self.filepath.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            # Ensure columns exist loosely
            required = {"Date", "Symbol", "Close"}
            if not required.issubset(set(reader.fieldnames or [])):
                raise ValueError(f"CSV must contain at least: {required}")

            for row in reader:
                d = datetime.strptime(row["Date"], "%Y-%m-%d").date()
                sym = row["Symbol"].upper()
                ohlc = OHLC(
                    open=float(row.get("Open", row["Close"])),
                    high=float(row.get("High", row["Close"])),
                    low=float(row.get("Low", row["Close"])),
                    close=float(row["Close"]),
                    volume=float(row.get("Volume", 0)) if "Volume" in row else None,
                )
                
                if d not in self._prices:
                    self._prices[d] = {}
                self._prices[d][sym] = ohlc

        self._days_sorted = sorted(self._prices.keys())

    def get_ohlc(self, day: date, symbols: Iterable[str]) -> Dict[str, OHLC]:
        day_prices = self._prices.get(day, {})
        return {s: day_prices[s] for s in symbols if s in day_prices}

    def next_trading_day_on_or_after(self, day: date) -> Optional[date]:
        for d in self._days_sorted:
            if d >= day:
                return d
        return None

    def trading_days(self) -> List[date]:
        return list(self._days_sorted)
