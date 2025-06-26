from openai import OpenAI

PROMPT = """\
// MQL5 Expert Advisor: STRAT EA with full optimization support.
//
// 1) Declare four input() parameters for optimization: MaximumRisk, DecreaseFactor, MAPeriod, MAShift.
// 2) Implement the STRAT logic: check 1h, 4h, 1d, 1w candles for same direction and open/close positions.
// 3) At the end of the test, compile balance and drawdown as usual.
// 4) Add an OnTester() function that returns win-percentage (wins/total trades * 100).
// 5) Use ORDER_TYPE_BUY/SELL for entries, and close any open position in OnDeinit() for final equity.
// 6) Follow MQL5 best practices (magic number, trade requests, error checks).
//  
// Generate a complete `.mq5` file named StratEA.mq5.
"""


def main() -> None:
    client = OpenAI()
    resp = client.completions.create(
        engine="code-davinci-002",
        prompt=PROMPT,
        max_tokens=2000,
        temperature=0,
    )
    mql5_code = resp.choices[0].text
    with open("StratEA.mq5", "w") as f:
        f.write(mql5_code)
    print("Wrote StratEA.mq5")


if __name__ == "__main__":
    main()
