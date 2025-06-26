# Strat-method

This repository provides an educational example of how you might structure an automated trading system using **The STRAT** methodology. The code is for informational purposes only and does **not** constitute financial advice.

The `strat_ea.py` script contains a minimal prototype EA. It can load price
data from CSV files or connect to a local MetaTrader 5 terminal. The EA checks
four time frames for trend alignment using a basic interpretation of **The
STRAT** and either performs a simple backtest or trades live using the
`run_live` helper.
A companion `StratEA.mq5` implements the strategy in MQL5 and exposes inputs for `MaximumRisk`, `DecreaseFactor`, `MAPeriod`, and `MAShift`.

## Usage

1. Install the optional Python packages: `pandas` (for faster CSV loading) and
   `MetaTrader5` if you want to trade live. The script will fall back to Python's
   built-in `csv` module when `pandas` is unavailable.
2. Place your OHLC CSV files in the `data/` directory or adjust the paths in
   `strat_ea.py`.
3. To backtest with the sample data, run `python strat_ea.py`.
4. To use MetaTrader 5, run something like:

   ```bash
   python strat_ea.py --live --symbol EURUSD --lot 0.1 --loops 10 --interval 60
   ```

   The EA will fetch fresh data every minute, align the four STRAT time frames,
   and place a market order if all point in the same direction. Make sure your
   MetaTrader 5 terminal is running and the symbol is available.

Always test strategies thoroughly on historical data and in simulation before risking real capital.

## Troubleshooting

If MetaTrader's *MetaEditor* shows many errors, you are likely attempting to
compile the wrong file.  **Compile `StratEA.mq5`, not `strat_ea.py`.**
The file `strat_ea.py` is pure Python and should be executed from a normal
Python interpreter using ``python strat_ea.py`` (add ``--live`` to connect to
MetaTrader 5).  Trying to compile the Python script in MetaEditor will produce
dozens of errors. If you see a long list of "undeclared identifier" messages,
open `StratEA.mq5` instead and compile that file.

## Generate MQL5 code with OpenAI

For convenience, `generate_mq5.py` can create a skeletal MQL5 Expert Advisor
using the OpenAI API. Install the `openai` package, set your `OPENAI_API_KEY`,
and run:

```bash
python generate_mq5.py
```

The script will write a new file `StratEA.mq5` in the repository root that you
can open in MetaEditor for compilation or further editing.

A ready-made `StratEA.mq5` is provided with four optimization inputs (`MaximumRisk`, `DecreaseFactor`, `MAPeriod`, and `MAShift`). Compile it in MetaEditor to run the EA.

