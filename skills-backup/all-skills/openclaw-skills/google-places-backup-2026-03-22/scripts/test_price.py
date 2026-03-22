#!/usr/bin/env python3
"""測試 Playwright 能否抓到 Google Maps 每人消費"""
import json
from playwright.sync_api import sync_playwright

PLACE_ID = "ChIJS2rX4KoXaTQRFmBySDRuXYc"
URL = f"https://www.google.com/maps/place/?q=place_id:{PLACE_ID}"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(URL, timeout=15000)
    page.wait_for_selector('button[aria-label*="per person"]', timeout=10000)

    el = page.query_selector('button[aria-label*="per person"]')
    aria = el.get_attribute("aria-label") if el else None
    print("ARIA:", aria)

    if el:
        el.click()
        page.wait_for_timeout(2000)

        # Try to read histogram table
        table = page.query_selector("table")
        if table:
            rows = table.query_selector_all("tr")
            for row in rows:
                cells = row.query_selector_all("td")
                if len(cells) >= 2:
                    print(f"  {cells[0].inner_text().strip()} | {cells[1].inner_text().strip()}")

    browser.close()
