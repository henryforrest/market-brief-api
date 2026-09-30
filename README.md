# Market Brief API

The Python backend for [Market Brief](https://apps.apple.com/us/app/market-brief-investing/id6758671631), my native iOS app for looking up the numbers serious investors actually care about — Sharpe ratio, maximum drawdown, annualised volatility, P/E — for any listed ticker. The iOS client sends a ticker; this service pulls a decade of daily prices from Yahoo Finance, computes the risk and return metrics server-side, attaches company fundamentals and a short LLM-written commentary, and returns it all as one JSON document. Keeping the maths on the server means the app renders rather than computes. There is a longer write-up in the [case study](https://henryforrest.github.io/market-brief.html).

## Endpoint

`GET /stock/{ticker}` — the ticker is upper-cased before use.

```
curl http://localhost:8080/stock/aapl
```

Response shape (values for Apple, September 2026, rounded):

```json
{
  "ticker": "AAPL",
  "name": "Apple Inc.",
  "price": 341.07,
  "market_cap": 4977636933632,
  "pe_ratio": 39.07,
  "max_drawdown": -0.374,
  "sharpe_ratio": 0.867,
  "annualized_return": 0.250,
  "volatility": 0.297,
  "sector": "Technology",
  "summary": {
    "name": "Apple Inc.",
    "sector": "Technology",
    "industry": "Consumer Electronics",
    "summary": "Apple Inc. designs, manufactures, and markets smartphones, ...",
    "website": "https://www.apple.com",
    "market_cap": 4977636933632
  },
  "ai_summary": "Summary: ...\nObservations: ...\nPrediction: ...\nReasons: ...\nRisks: ..."
}
```

Ratios are returned as decimals, not percentages (`-0.374` is a 37.4% drawdown). Fields Yahoo does not supply for a given instrument come back as `null`. A ticker Yahoo Finance has no price history for is returned as HTTP 404 with `{"detail": "Unknown ticker: ZZZZ"}`; the iOS app treats a 404 as an unknown ticker. Any other failure — an upstream data error, a model error — is returned as HTTP 500 with the exception message in `detail`. FastAPI's interactive docs are served at `/docs`.

## Metrics

The four risk/return metrics are computed in `get_metrics.py` from daily closing prices fetched with `yfinance` (`Ticker.history`) from 1 January 2015 to the present, using simple daily returns (`pct_change`) and a 252-trading-day year. The price series is selected in one place, `get_data.get_prices`: the adjusted close where Yahoo supplies one, otherwise the close, which `history()` returns already adjusted for splits and dividends.

- **Maximum drawdown** — prices are normalised to the first observation, the running peak is tracked with `cummax`, and the drawdown series is `equity / peak - 1`; the metric is its minimum, i.e. the worst peak-to-trough fall over the whole window.
- **Sharpe ratio** — daily excess returns are the daily returns less a 1% annual risk-free rate divided by 252; the ratio is their mean over their standard deviation, annualised by √252. Returns `0.0` if the standard deviation is zero or non-finite.
- **Annualised return** — the compound growth of the whole series, `prod(1 + r)`, raised to `1 / (n / 252)`, minus one: a CAGR over the lookback window.
- **Volatility** — the standard deviation of daily returns multiplied by √252.

`price`, `market_cap`, `pe_ratio`, `name` and `sector` are read straight from `yfinance`'s `Ticker.info` (`currentPrice`, `marketCap`, `trailingPE`, `shortName`, `sector`), so the P/E is the trailing ratio. The nested `summary` object adds `industry`, the long business description and the company website from the same source.

## AI summary

`ai_summary.py` calls the Hugging Face Inference Providers router (`https://router.huggingface.co/v1/chat/completions`, an OpenAI-compatible chat completions API) with `meta-llama/Llama-3.1-8B-Instruct`, `max_tokens` 1000 and a 30-second timeout. The model is given the ticker and the complete metrics-and-fundamentals dictionary above, told to use only that data, and asked for five labelled sections: a short summary, two observations, an UP/DOWN call for the next one to two weeks, the reasons for it, and one risk to watch. The reply is returned verbatim as the `ai_summary` string.

The token is read from the `HF_TOKEN` environment variable when the module is imported; `python-dotenv` first loads a `.env` file from the project directory if one exists. Without the variable the process does not start.

## Stack

- Python 3.11, FastAPI, Uvicorn
- `yfinance` (Yahoo Finance) for prices and fundamentals, with pandas and NumPy for the metrics
- `requests` to the Hugging Face Inference Providers router; Llama 3.1 8B Instruct writes the commentary
- Docker, Fly.io (London region), GitHub Actions

## Running locally

```
git clone https://github.com/henryforrest/market-brief-api.git
cd market-brief-api
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
echo "HF_TOKEN=<your Hugging Face token>" > .env    # or export HF_TOKEN=...
uvicorn main:app --host 0.0.0.0 --port 8080
curl http://localhost:8080/stock/AAPL
```

Or with Docker — `.dockerignore` keeps `.env` out of the image, so the token has to be passed in:

```
docker build -t market-brief-api .
docker run -p 8080:8080 -e HF_TOKEN=<your Hugging Face token> market-brief-api
```

## Tests

The suite in `tests/` runs offline: `yfinance` is stubbed with canned price history and fundamentals and the Hugging Face call is replaced, so no test touches the network or needs a real token.

```
pip install -r requirements.txt -r requirements-dev.txt
python -m pytest -q
```

It checks the metrics against small synthetic series with known answers (a flat series gives zero for every metric, a 50% fall from the peak gives a drawdown of `-0.5`, a year of constant daily growth gives the compounded rate, and a frame whose Open and Close columns differ proves the metrics follow Close), the price selection (adjusted close preferred, close otherwise) and the endpoint through FastAPI's `TestClient` (the full response document, the upper-cased ticker, 404 for an unknown ticker and 500 with the message for anything else). `.github/workflows/tests.yml` runs the suite on every push and pull request with Python 3.11.

## Deployment

The `Dockerfile` starts from `python:3.11-slim`, installs `requirements.txt`, copies the source and runs `uvicorn main:app --host 0.0.0.0 --port 8080`. `fly.toml` deploys that image to Fly.io as a single shared-CPU, 512 MB machine in `lhr`, with HTTPS forced at Fly's edge, the app listening on port 8080, and machines that stop when idle and start again on the next request (`min_machines_running = 0`).

Deploys are automatic: `.github/workflows/fly-deploy.yml` runs `flyctl deploy --remote-only` on every push to `main`, authenticated with a `FLY_API_TOKEN` repository secret, under a concurrency group so only one deploy runs at a time. `HF_TOKEN` is held in Fly's secrets rather than in the image.
