from bs4 import BeautifulSoup
import requests
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
def fetch_content(url:str) -> str:
    # url = f"https://groww.in/mutual-funds/{uri}"
    print(f"Processing: {url}")
    resp = requests.get(url)
    return resp.text

def scrape_MF_web_page(url: str) -> list[dict]:
    """
    Scrape the stock holdings table from the given URL.

    Args:
        text
    Returns:
        list[dict]: A list of dictionaries, each containing the Name, Sector, Instrument, Assets, and Link.
    """
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
            if instrument=="Equity" and float(assets.replace("%",""))>0: stocks += ({'name':name,'Link':link},)
        # with ThreadPoolExecutor(max_workers=20) as executor:
        #     # Submit all tasks
        #     futures = [executor.submit(get_element_text, f"https://groww.in{stock['Link']}",idx) for idx,stock in enumerate(data) if stock.get("Link") and stock.get('Instrument')=='Equity']
        #     # Process results as they complete
        #     for future in as_completed(futures):
                
        #         stock_data, idx = future.result()
        #         print(stock_data)
        #         data[idx].update(stock_data)
        mf_name = url.split("/")[-1]
        json_path = os.path.join("mutual_fund_jsons", f"{mf_name}.json")
        with open(json_path, "w", encoding='utf-8') as jsonfile:
            json.dump(data, jsonfile, indent=2, ensure_ascii=False)

        return (mf_name, stocks, "Success")
    except Exception as e:
        print(f"[!] Error processing {url}: {e}")
        return (url, (), "failed")

from playwright.sync_api import sync_playwright

def get_element_text_(url: str,idx) -> str:
    print(f"Processing : {url}")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, timeout=5000)  # wait up to 60s

        # Wait for the element to appear (optional but recommended)
        page.wait_for_selector("#root > div:nth-child(2) > div.container.web-align > div > div > div.pw14ContentWrapper.backgroundPrimary.layout-main.width100 > div.width100.stkP12BelowFoldDiv > div.lpu38MainDiv > div.lpu38HeadWrap > div:nth-child(3)", timeout=30000)

        element = page.query_selector("#root > div:nth-child(2) > div.container.web-align > div > div > div.pw14ContentWrapper.backgroundPrimary.layout-main.width100 > div.width100.stkP12BelowFoldDiv > div.lpu38MainDiv > div.lpu38HeadWrap > div:nth-child(3)")
        if element:
            result = element.inner_text()
            browser.close()
            result = result.split('\n')
            result += result.pop(-1).split()
            return dict(zip(['currency','price','absolute_change','percentage_change','time_frame'],result)),idx
        else:
            browser.close()
            return {}, idx

def get_element_text(url: str, idx: int) -> tuple[dict, int]:
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=50000)
            page.wait_for_selector(".lpu38HeadWrap div:nth-child(3)", timeout=50000)

            element = page.query_selector(".lpu38HeadWrap div:nth-child(3)")
            if element:
                result = element.inner_text()
                result = result.split('\n')
                result += result.pop(-1).split()
                return dict(zip(['currency','price','absolute_change','percentage_change','time_frame'], result)), idx
            else:
                return {}, idx
    except Exception as e:
        print(f"[!] Error scraping {url}: {e}")
        return {}, idx

if __name__ == "__main__":
    os.makedirs("mutual_fund_jsons", exist_ok=True)

    # Read mutual fund URLs
    with open("mutual_funds", "r") as f:
        mfs = [line.strip() for line in f if line.strip()]

    urls = [f"https://groww.in/mutual-funds/{mf}" for mf in mfs]

    start = time.time()

    # ThreadPoolExecutor for I/O-bound task
    with ThreadPoolExecutor(max_workers=10) as executor:
        # Submit all tasks
        futures = [executor.submit(scrape_MF_web_page, url) for url in urls]

        # Process results as they complete
        all_stocks = ()
        for future in as_completed(futures):
            _url, _stocks, _status = future.result()
            all_stocks += _stocks
            if _status == "Success":
                print(f"Successfully saved {len(_stocks)} stocks for {_url} to track")
            else:
                print(f"Failed to process {_url}")
        print(f"Total stocks to track: {len(all_stocks)}")
        with open("mf_stocks.json", "w", encoding='utf-8') as jsonfile:
            json.dump(all_stocks, jsonfile, indent=2, ensure_ascii=False)

    end = time.time()
    print(f"All tasks completed in {end - start:.2f} seconds")
