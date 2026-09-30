from fastapi import FastAPI, HTTPException
from market_data import fetch_stock_data
from get_data import TickerNotFoundError
from ai_summary import generate_ai_summary
import traceback

app = FastAPI()

@app.get("/stock/{ticker}")
def get_stock(ticker: str):
    try:
        stock_data = fetch_stock_data(ticker)
        ai_summary = generate_ai_summary(ticker, stock_data)


        return {
            **stock_data,
            "ai_summary": ai_summary
        }

    except TickerNotFoundError:
        raise HTTPException(status_code=404, detail=f"Unknown ticker: {ticker.upper()}")

    except Exception as e:
        print("ERROR:", repr(e))
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

