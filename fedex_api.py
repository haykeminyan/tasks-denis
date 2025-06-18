import aiohttp
import asyncio
import random
from fastapi import FastAPI
from models import TrackRequest
from FakeAgent import Fake_Agent

app = FastAPI()


async def fetch_fedex(tracking_id: str, max_retries: int = 10, delay_range=(1, 2)):
    url = f'https://www.fedex.com/fedextrack/system-error?trknbr={tracking_id}'
    retries = 0

    async with aiohttp.ClientSession() as session:
        while retries < max_retries:
            ua = Fake_Agent().random()
            # until we dont get 200 we will send request (max: 10)
            try:
                async with session.get(url, headers={'User-Agent': ua}, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 200:
                        return {
                            "status": 200,
                            "tracking_id": tracking_id,
                            "url": str(resp.url)
                        }
                    else:
                        print(f"[{resp.status}] Retry: {url}")
            except Exception as e:
                print(f"[ERROR] {url} — {e}")

            retries += 1
            await asyncio.sleep(random.uniform(*delay_range))

    return {
        "status": "error",
        "tracking_id": tracking_id,
        "url": url
    }


@app.post("/track")
async def track(req: TrackRequest):
    return await fetch_fedex(req.tracking_id, req.max_retries)
