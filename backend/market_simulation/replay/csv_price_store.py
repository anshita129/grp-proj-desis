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
            fieldnames = set(reader.fieldnames or [])

            # Support both title and lower case headers
            date_col = "Date" if "Date" in fieldnames else "timestamp"
            sym_col = "Symbol" if "Symbol" in fieldnames else "symbol"
            close_col = "Close" if "Close" in fieldnames else "close"
            open_col = "Open" if "Open" in fieldnames else "open"
            high_col = "High" if "High" in fieldnames else "high"
            low_col = "Low" if "Low" in fieldnames else "low"
            vol_col = "Volume" if "Volume" in fieldnames else "volume"

            if close_col not in fieldnames or sym_col not in fieldnames or date_col not in fieldnames:
                raise ValueError(f"CSV missing required columns. Found: {fieldnames}")

            for row in reader:
                # Handle either ISO date or full timestamp string
                date_str = row[date_col].split(" ")[0]
                d = datetime.strptime(date_str, "%Y-%m-%d").date()
                sym = row[sym_col].upper()
                ohlc = OHLC(
                    open=float(row.get(open_col, row[close_col])),
                    high=float(row.get(high_col, row[close_col])),
                    low=float(row.get(low_col, row[close_col])),
                    close=float(row[close_col]),
                    volume=float(row.get(vol_col, 0)) if vol_col in row else None,
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
