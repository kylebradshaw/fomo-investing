# FOMO INVESTING

## INSTALLATION

```bash
pip install -r requirements.txt
```

## ANALYZE A PORTFOLIO with `fomo.py`

This script calculates the value changes of a specified portfolio of stocks over a given date range. It can also save the execution history and aggregate results from past executions.

```bash
python fomo.py --portfolio=VTSAX(485.113),VOO(40.000) --from=2024.05.28 --to=2024.06.11
```

## HOWTO

### Command-line Arguments

- `--portfolio` specifies the portfolio of tickers and shares, e.g., `'VTSAX(485.113),VOO(40.000)'`.
- `--from` specifies the start date in `YYYY.MM.DD` format.
- `--to` specifies the end date in `YYYY.MM.DD` format (optional). Defaults to the previous market close if not provided.
- `--aggregate` runs all recorded commands from the history file.
- `--save` saves the command to the history file if it's unique for the given portfolio and date.

### History File

- The script appends each execution to `portfolio_history.csv` if the `--save` flag is used.
- The `save_to_history` function checks for duplicates before saving to ensure only unique entries per portfolio and date are saved.

### Aggregate Execution

- When `--aggregate` is specified, the script runs calculations for all recorded portfolios in the history file.

## Usage Examples

### Run a new command and save to history

```bash
python fomo.py --portfolio="VTSAX(485.113),VOO(40.000)" --from=2024.05.28 --to=2024.06.11 --save
```

```bash
python fomo.py --portfolio="MSTR(25.000),FBTC(689.000)" --from=2024.05.29 --to=2024.06.11 --save
```
