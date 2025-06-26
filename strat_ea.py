"""Prototype STRAT-based trading strategy.

This **Python** script demonstrates a minimal example of how an Expert
Advisor (EA) could apply Rob Smith's STRAT method across four time frames.
Run it with ``python strat_ea.py`` or ``python -m strat_ea``
from a regular Python environment.  **Do not try to compile this file in
MetaTrader's MetaEditor.**  A separate ``StratEA.mq5`` is provided for MQL5
users. If MetaEditor reports dozens of errors, you're compiling this Python
file instead of the ``.mq5`` source.

The code is provided for educational purposes only and does not constitute
financial advice. Use at your own risk.
"""
from dataclasses import dataclass
from typing import Dict, List, Optional
import csv
import time

try:  # pandas provides convenience but is optional
    import pandas as pd
except ImportError:  # pragma: no cover - fallback to csv reader
    pd = None
    print("pandas not found; using built-in csv module", flush=True)

try:
    import MetaTrader5 as mt5
except ImportError:  # pragma: no cover - MT5 optional
    mt5 = None

@dataclass
class Candle:
    open: float
    high: float
    low: float
    close: float

def candle_direction(candle: Candle, min_body_ratio: float = 0.0) -> Optional[str]:
    """Determine candle direction if body exceeds minimum ratio of range."""
    candle_range = candle.high - candle.low
    if candle_range <= 0:
        return None
    body = candle.close - candle.open
    body_size = abs(body)
    if body_size < min_body_ratio * candle_range:
        return None
    return 'up' if body > 0 else 'down'

def analyze_timeframes(timeframes: Dict[str, List[Candle]], min_body_ratio: float = 0.0) -> Optional[str]:
    """Check multiple time frames for the same direction."""
    directions = []
    for tf, candles in timeframes.items():
        if not candles:
            return None
        direction = candle_direction(candles[-1], min_body_ratio)
        if direction is None:
            return None
        directions.append(direction)
    return directions[0] if all(d == directions[0] for d in directions) else None

def aggregate_signal(timeframes: Dict[str, List[Candle]], min_body_ratio: float = 0.0) -> str:
    """Generate buy, sell, or hold signal for multiple time frames."""
    direction = analyze_timeframes(timeframes, min_body_ratio)
    if direction == 'up':
        return 'buy'
    if direction == 'down':
        return 'sell'
    return 'hold'


def load_csv_files(files: Dict[str, str]) -> Dict[str, List[Candle]]:
    """Load OHLC data from CSV files for each timeframe."""
    data: Dict[str, List[Candle]] = {}
    for tf, path in files.items():
        if pd is not None:
            df = pd.read_csv(path)
            rows = (
                (row.open, row.high, row.low, row.close)
                for row in df.itertuples(index=False)
            )
        else:
            with open(path, newline="") as f:
                reader = csv.reader(f)
                next(reader, None)  # skip header
                rows = [
                    (float(o), float(h), float(l), float(c))
                    for o, h, l, c in reader
                ]
        candles = [Candle(o, h, l, c) for o, h, l, c in rows]
        data[tf] = candles
    return data


def load_mt5_data(symbol: str, bars: int = 200) -> Dict[str, List[Candle]]:
    """Fetch OHLC data from MetaTrader 5 for the main STRAT time frames."""
    if mt5 is None:
        raise RuntimeError("MetaTrader5 package is not available")
    tf_map = {
        "1h": mt5.TIMEFRAME_H1,
        "4h": mt5.TIMEFRAME_H4,
        "1d": mt5.TIMEFRAME_D1,
        "1w": mt5.TIMEFRAME_W1,
    }
    data: Dict[str, List[Candle]] = {}
    for name, mt5_tf in tf_map.items():
        rates = mt5.copy_rates_from_pos(symbol, mt5_tf, 0, bars)
        candles = [
            Candle(r.open, r.high, r.low, r.close)
            for r in rates
        ]
        data[name] = candles
    return data


class StratEA:
    """Simple STRAT-based EA using multiple time frames."""

    def __init__(self, data: Dict[str, List[Candle]], min_body_ratio: float = 0.1):
        self.data = data
        self.min_body_ratio = min_body_ratio
        self.position: Optional[str] = None
        self.entry_price: Optional[float] = None
        self.balance = 0.0

    def _price_at(self, index: int) -> float:
        # Use the closing price of the smallest timeframe as execution price
        smallest_tf = sorted(self.data.keys())[0]
        return self.data[smallest_tf][index].close

    def signal_for_index(self, index: int) -> str:
        """Generate signal for a specific candle index."""
        slices = {tf: candles[: index + 1] for tf, candles in self.data.items()}
        return aggregate_signal(slices, self.min_body_ratio)

    def step(self, index: int) -> None:
        signal = self.signal_for_index(index)
        price = self._price_at(index)
        if signal == 'buy' and self.position != 'long':
            if self.position == 'short':
                self.balance += self.entry_price - price
            self.position = 'long'
            self.entry_price = price
        elif signal == 'sell' and self.position != 'short':
            if self.position == 'long':
                self.balance += price - self.entry_price
            self.position = 'short'
            self.entry_price = price

    def backtest(self) -> float:
        length = min(len(c) for c in self.data.values())
        for i in range(length):
            self.step(i)
        # close any open trade at final price
        final_price = self._price_at(length - 1)
        if self.position == 'long':
            self.balance += final_price - self.entry_price
        elif self.position == 'short':
            self.balance += self.entry_price - final_price
        self.position = None
        return self.balance


def place_market_order(symbol: str, action: str, lot: float = 0.1) -> None:
    """Send a market order via MetaTrader 5."""
    if mt5 is None:
        raise RuntimeError("MetaTrader5 package is not available")
    if action == "buy":
        order_type = mt5.ORDER_TYPE_BUY
        price = mt5.symbol_info_tick(symbol).ask
    else:
        order_type = mt5.ORDER_TYPE_SELL
        price = mt5.symbol_info_tick(symbol).bid
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot,
        "type": order_type,
        "price": price,
        "deviation": 10,
        "magic": 123456,
        "comment": "STRAT EA",
    }
    result = mt5.order_send(request)
    print(f"Order send result: {result}")


def run_live(
    symbol: str,
    bars: int = 200,
    lot: float = 0.1,
    min_body_ratio: float = 0.1,
    interval: int = 60,
    loops: int = 1,
) -> None:
    """Run the EA in live mode, submitting orders via MetaTrader 5."""
    if mt5 is None:
        raise RuntimeError("MetaTrader5 package is required for live mode")
    if not mt5.initialize():
        raise RuntimeError("MetaTrader5 initialization failed")
    try:
        for _ in range(loops):
            data = load_mt5_data(symbol, bars=bars)
            ea = StratEA(data, min_body_ratio=min_body_ratio)
            index = len(data["1h"]) - 1
            signal = ea.signal_for_index(index)
            print(f"Trading signal: {signal}")
            if signal in ("buy", "sell"):
                place_market_order(symbol, signal, lot=lot)
            if loops > 1:
                time.sleep(interval)
    finally:
        mt5.shutdown()

# Example usage with MetaTrader 5 or CSV data
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="STRAT EA prototype")
    parser.add_argument("--symbol", default="EURUSD", help="Trading symbol")
    parser.add_argument("--live", action="store_true", help="Use MetaTrader 5")
    parser.add_argument("--bars", type=int, default=200, help="Number of bars to load")
    parser.add_argument("--lot", type=float, default=0.1, help="Lot size for live trades")
    parser.add_argument("--min-body", type=float, default=0.1, help="Minimum candle body ratio")
    parser.add_argument("--interval", type=int, default=60, help="Seconds between live checks")
    parser.add_argument("--loops", type=int, default=1, help="Number of live iterations")
    args = parser.parse_args()

    if args.live:
        run_live(
            args.symbol,
            bars=args.bars,
            lot=args.lot,
            min_body_ratio=args.min_body,
            interval=args.interval,
            loops=args.loops,
        )
    else:
        files = {
            "1h": "data/1h.csv",
            "4h": "data/4h.csv",
            "1d": "data/1d.csv",
            "1w": "data/1w.csv",
        }
        data = load_csv_files(files)
        ea = StratEA(data, min_body_ratio=0.1)
        profit = ea.backtest()
        print(f"Backtest result: {profit:.2f} units")
