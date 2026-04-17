# EV Resale Calculator

This tool helps estimate whether sealed card product is worth buying for resale.
It reads a card price CSV, estimates expected pulls by rarity, subtracts selling
fees, applies a realistic sale-price adjustment, and reports break-even buy
prices for a case, box, and pack.

## Setup

Install Python 3.10 or newer, then run:

```bash
pip install -r requirements.txt
```

## Easy mode

Run:

```bash
python evcal.py
```

The app will ask for a CSV file, Google Drive CSV share link, or direct CSV URL.
It will then ask for product type, pull rates, buy cost, selling fees, and the
percent of market price you expect to actually receive.

## Command line mode

```bash
python evcal.py --csv prices.csv --case-cost 850 --fee-percent 13 --price-adjustment-percent 90
```

Optional example with a saved breakdown:

```bash
python evcal.py --csv prices.csv --case-cost 850 --output ev_breakdown.csv
```

## CSV columns

The CSV should include a price column and a rarity column. The script looks for
common TCGplayer-style columns such as:

- `TCG Market Price`
- `Market Price`
- `Price`
- `Rarity`
- `Product Name`

If a product name contains terms like `alternate art`, `alt art`, or `parallel`,
the card is counted as `alternate art`.

## How to read the result

- `Gross market EV` is the raw expected value using listed market prices.
- `Net resale EV` is after your sale-price adjustment and marketplace fees.
- `Expected profit/loss` compares net resale EV to your buy cost.
- `Break-even max buy prices` are the most you should pay before expected profit
  becomes zero.

This is still an estimate. Real results can change because of pull-rate variance,
shipping costs, taxes, condition issues, and how fast cards actually sell.
