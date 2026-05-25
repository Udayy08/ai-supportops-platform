import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        page.set_default_timeout(30000)
        
        print("Navigating to evaluations page...")
        await page.goto("http://localhost:3000/evaluations")
        
        # Wait for metrics to load
        await page.wait_for_selector("text=Retrieval Health Score", state="visible")
        # Give it a second for charts and tables to finish rendering
        await page.wait_for_timeout(2000)
        
        print("Taking KPI Dashboard screenshot...")
        await page.screenshot(path="kpi_dashboard.png")
        
        print("Taking Trend Charts screenshot...")
        await page.evaluate("window.scrollBy(0, 300)")
        await page.wait_for_timeout(500)
        await page.screenshot(path="trend_charts.png")
        
        print("Taking Document Analytics screenshot...")
        await page.evaluate("window.scrollBy(0, 500)")
        await page.wait_for_timeout(500)
        await page.screenshot(path="document_analytics.png")
        
        print("Taking Failure Analytics screenshot...")
        # Scroll down to failure analytics
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await page.wait_for_timeout(500)
        await page.screenshot(path="failure_analytics.png")
        
        # Take full page screenshot just in case
        await page.screenshot(path="retrieval_health_score.png", full_page=True)
        
        await browser.close()
        print("Done.")

if __name__ == "__main__":
    asyncio.run(main())
