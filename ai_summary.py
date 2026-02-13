import os
import requests
from dotenv import load_dotenv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

HF_TOKEN = os.environ["HF_TOKEN"]

def generate_ai_summary(ticker: str, metrics: dict) -> str:
    prompt = f"""You are an investment analyst. Using ONLY the data below, provide:

                                1) A short summary of the stock: {ticker}
                                2) 2 interesting observations.
                                3) A prediction (UP or DOWN) for the next 1–2 weeks.
                                4) 1–2 reasons for your prediction.
                                5) 1 risk/uncertainty to watch.

                                DATA:
                                {metrics}

                                OUTPUT FORMAT:
                                Summary:
                                Observations:
                                Prediction:
                                Reasons:
                                Risks:
                                """

    response = requests.post(
        "https://router.huggingface.co/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {HF_TOKEN}",
            "Content-Type": "application/json"
        },
        json={
            "model": "meta-llama/Llama-3.1-8B-Instruct",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1000
        },
        timeout=30
    )

    print("AI RESPONSE STATUS:", response.status_code)
    print("AI RESPONSE:", response.json())

    return response.json()["choices"][0]["message"]["content"]
