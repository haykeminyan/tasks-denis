import requests
from FakeAgent import Fake_Agent
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import random

tracking_ids = [str(12312341 + i) for i in range(100)]  # или 1000+

def fetch_until_success(url, max_retries=9999, delay_range=(1, 3)):
    retries = 0
    while retries < max_retries:
        ua = Fake_Agent().random()
        try:
            r = requests.get(url, headers={'User-Agent': ua}, timeout=10)
            if r.status_code == 200:
                print("200 заебись")
                return url, 200
            else:
                print(f"️ [{r.status_code}] {url} — ебём дальше..")
        except Exception as e:
            print(f"{url} — {e}")

        retries += 1
        time.sleep(random.uniform(*delay_range))

    return url, None

def main():
    urls = [f'https://www.fedex.com/wtrk/track/?tracknumbers={tid}' for tid in tracking_ids]

    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = [executor.submit(fetch_until_success, url) for url in urls]

        for future in as_completed(futures):
            url, status = future.result()
            if status == 200:
                print(f" Успех: {url}")
            else:
                print(f" Провал: {url} — не смог получить 200")

if __name__ == '__main__':
    main()
