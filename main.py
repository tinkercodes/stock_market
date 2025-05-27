import os
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup
import requests
import asyncio
from tabulate import tabulate
from playwright.async_api import async_playwright

from async_scraper import get_element_text

def fetch_content(url: str) -> str:
    print(f"Processing: {url}")
    resp = requests.get(url)
    return resp.text

# Helper: break list into chunks
def chunkify(lst, chunk_size):
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]

async def run_stock_tasks(stocks: dict, chunk_size: int = 30) -> list[dict]:
    # Step 1: Save original index to each stock
    for idx, stock in enumerate(stocks):
        stock["original_index"] = idx

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        # Step 2: Process in chunks
        for stock_chunk in chunkify(stocks, chunk_size):
            context = await browser.new_context()

            tasks = []
            for stock in stock_chunk:
                url = f"https://groww.in{stock['Link']}"
                tasks.append(get_element_text(context, url, stock["original_index"]))

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Step 3: Update original stocks list
            for result in results:
                if isinstance(result, Exception):
                    continue  # handle or log error if needed
                stock_data, original_index = result
                stocks[original_index].update(stock_data)

            await context.close()

        await browser.close()

    # Step 4: Clean up the helper index
    for stock in stocks:
        stock.pop("original_index", None)

    return stocks


def scrape_MF_web_page(url: str) -> tuple[str, str]:
    try:
        text = fetch_content(url)
        soup = BeautifulSoup(text, "html.parser")
        table = soup.find("table", class_="holdings101Table")

        if not table:
            raise ValueError("Holdings table not found on the page.")

        rows = table.find("tbody").find_all("tr")
        stocks = ()
        data = []
        for row in rows:
            cols = row.find_all("td")
            if len(cols) != 4:
                continue
            link_tag = cols[0].find("a")
            name = link_tag.get_text(strip=True) if link_tag else cols[0].get_text(strip=True)
            link = link_tag["href"] if link_tag and link_tag.has_attr("href") else None
            sector = cols[1].get_text(strip=True)
            instrument = cols[2].get_text(strip=True)
            assets = cols[3].get_text(strip=True)
            data.append({
                "Name": name,
                "Sector": sector,
                "Instrument": instrument,
                "Assets": assets,
                "Link": link
            })
            if instrument=="Equity" and float(assets.replace("%",""))>0 and link: 
                stocks += ({'name': name, 'Link': link},)

        mf_name = url.split("/")[-1]
        json_path = os.path.join("mutual_fund_jsons", f"{mf_name}.json")
        with open(json_path, "w", encoding='utf-8') as jsonfile:
            json.dump(data, jsonfile, indent=2, ensure_ascii=False)

        return (mf_name, stocks, "Success")
    except Exception as e:
        print(f"[!] Error processing {url}: {e}")
        return (url, (), "failed")

def main(mfs: list[str] = None):
    os.makedirs("mutual_fund_jsons", exist_ok=True)

    urls = [f"https://groww.in/mutual-funds/{mf}" for mf in mfs]
    all_stocks = ()
    start = time.time()
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(scrape_MF_web_page, url) for url in urls]
        
        for future in as_completed(futures):
            _url, _stocks, _status = future.result()
            all_stocks += _stocks
            if _status == "Success":
                print(f"Successfully saved {len(_stocks)} stocks for {_url} to track")
            else:
                print(f"Failed to process {_url}")
        print(f"Total stocks to track: {len(all_stocks)}")

    print("Starting async tasks for stock data scraping...")
    asyncio.run(run_stock_tasks(list(all_stocks)))  # Call async tasks here
    print("Async tasks completed, saving results...")
    # Save all stocks to a JSON file
    stocks_dict = {stock['Link'].split("/")[-1]: stock for stock in all_stocks}
    with open("mf_stocks.json", "w", encoding='utf-8') as jsonfile:
        json.dump(stocks_dict, jsonfile, indent=2, ensure_ascii=False)
    end = time.time()
    print(f"All tasks completed in {end - start:.2f} seconds")

def calculate_mf_percentage_change(mfs: list[str] = None):
    with open("mf_stocks.json", "r") as jsonfile:
        stocks = json.load(jsonfile)

    for mf in mfs:
        mf_name = mf.split("/")[-1]
        json_path = os.path.join("mutual_fund_jsons", f"{mf_name}.json")
        if not os.path.exists(json_path):
            continue

        with open(json_path, "r") as f:
            mf_data = json.load(f)
        table=[]
        mf_percentage_change = 0
        for stock in mf_data:
            stocks_id = stock["Link"].split("/")[-1]
            stock_weight = float(stock['Assets'].replace("%",""))
            stock_ = stocks.get(stocks_id, {})
            stock_change = float(stock_.get('percentage_change', '(0%)')[1:-2])
            signed_stock_change = stock_change * -1 if stock_['absolute_change'].startswith('-') else stock_change
            mf_percentage_change += signed_stock_change * stock_weight / 100
        table.append([" ".join(mf_name.split('-')).capitalize(), f"{mf_percentage_change:.2f}%"])
        
    headers = ["Mutual Fund", "Percentage Change"]

    print("Report Summary>>\n",tabulate(table, headers=headers, tablefmt="fancy_grid"))
    with open("report_summary.md", "w") as f:
        f.write("# Mutual Fund Report Summary\n\n")
        f.write(tabulate(table, headers=headers, tablefmt="github"))
        f.write("\n\n> **Note:** Percentage change is calculated based on the weight of each stock in the mutual fund.")

    

if __name__ == "__main__":
    with open("mutual_funds", "r") as f:
        mfs = [line.strip() for line in f if line.strip()]
    main(mfs)
    calculate_mf_percentage_change(mfs)
