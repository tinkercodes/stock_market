# async_scraper.py
import asyncio
from playwright.async_api import async_playwright

async def get_element_text(context, url: str, idx: int) -> tuple[dict, int]:
    page = await context.new_page()
    stock_data = {}
    try:
        await page.goto(url, timeout=300000)
        await page.wait_for_selector(".lpu38HeadWrap div:nth-child(3)", timeout=100000)
        element = await page.query_selector(".lpu38HeadWrap div:nth-child(3)")
        if element:
            result = await element.inner_text()
            result = result.split('\n')
            result += result.pop(-1).split()
            stock_data = dict(zip(['price', 'absolute_change', 'percentage_change', 'time_frame'], result))
    except Exception as e:
        print(f"[!] Error scraping {url}: {e}")
    finally:
        await page.close()
        # print(f"Processed: {url} \nResult: {stock_data}")
        return stock_data, idx


# Optional: if you want to test this module standalone
if __name__ == "__main__":
    async def test():
        url = "https://groww.in/stocks/pfizer-ltd"  # example stock URL
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            result = await get_element_text(context, url, 0)
            print(result)

    asyncio.run(test())
