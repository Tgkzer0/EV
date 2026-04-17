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
It will then ask for product layout, pull rates, buy cost, selling fees, and
the percent of market price you expect to actually receive.

The calculator no longer assumes chase cards are guaranteed. If your price CSV
has pull-rate columns, it will use them. If not, the app can ask for a separate
pull-rate CSV or let you enter expected pulls per case manually.

## Command line mode

```bash
python evcal.py --csv prices.csv --case-cost 850 --fee-percent 13 --price-adjustment-percent 90
```

Optional example with a saved breakdown:

```bash
python evcal.py --csv prices.csv --case-cost 850 --output ev_breakdown.csv
```

Optional example with a separate rarity spread file:

```bash
python evcal.py --csv prices.csv --pull-rates pull_rates.csv --case-cost 850
```

Example for a product with custom pack and case layout:

```bash
python evcal.py --csv prices.csv --packs-per-box 36 --boxes-per-case 6 --cards-per-pack 15 --case-cost 720
```

Example for products sold as loose packs per case:

```bash
python evcal.py --csv prices.csv --packs-per-case 144 --cards-per-pack 10 --case-cost 500
```

You can also enter expected pulls directly from the command line:

```bash
python evcal.py --csv prices.csv --packs-per-case 144 --pull "ultra rare=3" --pull "secret rare=1.2"
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

## Pull-rate columns

The price CSV or a separate `--pull-rates` CSV can include rarity spread data.
Use a `Rarity` column plus one of these formats. Rarity names are not limited to
one game, so names like `ultra rare`, `mythic`, `holo rare`, `foil`, `legendary`,
or game-specific terms are all allowed.

```csv
Rarity,Pulls Per Case
super rare,84
secret rare,2
alternate art,1.5
```

```csv
Rarity,Pull Rate Percent
secret rare,0.7
alternate art,0.5
```

```csv
Rarity,One Per Packs
secret rare,144
alternate art,192
```

`Pulls Per Case` is the clearest option. The percent and one-per-pack formats
are converted into expected pulls based on the configured packs per box and
boxes per case.

If you enter only chase-card odds, the normal rare-slot count is reduced so the
same pack slot is not counted twice.

## Product layout

For each product, set:

- `packs per box`
- `boxes per case`
- `cards per pack`
- expected rarity slots per pack or per case

If the product is not packaged as boxes inside a case, use `--packs-per-case`.
That treats the case as one container with that many packs.

The app does not automatically scrape pack configurations from the web because
TCG rarity spreads are often unofficial, regional, or product-specific. The safer
workflow is to enter the product layout from a reliable source, then save it as a
pull-rate CSV for reuse.

## How to read the result

- `Gross market EV` is the raw expected value using listed market prices.
- `Net resale EV` is after your sale-price adjustment and marketplace fees.
- `Expected profit/loss` compares net resale EV to your buy cost.
- `Break-even max buy prices` are the most you should pay before expected profit
  becomes zero.

This is still an estimate. Real results can change because of pull-rate variance,
shipping costs, taxes, condition issues, and how fast cards actually sell.
