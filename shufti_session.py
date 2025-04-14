# shufti_session.py
import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup

BASE_URL = "https://app.shufti.jp/jobs/search"
LOGIN_URL = "https://app.shufti.jp/login"

class MessagingAgent:
    def send_message(self, job_id, message):
        print(f"Sending message for Job {job_id}: {message}")
        return True

class JobScraper:
    def __init__(self, email, password, max_pages=2, delay=5):
        self.email = email
        self.password = password
        self.max_pages = max_pages
        self.delay = delay

    async def login(self, page):
        await page.goto(LOGIN_URL, timeout=30000)
        await page.wait_for_timeout(3000)
        await page.fill("#username", self.email)
        await page.fill("#password", self.password)
        await page.wait_for_selector("#submit:not([disabled])", timeout=10000)
        await page.click("#submit")
        await page.wait_for_timeout(5000)

    async def crawl_jobs(self):
        jobs = []
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            await self.login(page)

            for page_num in range(1, self.max_pages + 1):
                await page.goto(f"{BASE_URL}?page={page_num}", timeout=30000)
                await asyncio.sleep(self.delay)

                html = await page.content()
                soup = BeautifulSoup(html, "html.parser")

                job_cards = soup.find_all("a", class_="job-info-full-link")
                for card in job_cards:
                    job_url = "https://app.shufti.jp" + card['href']
                    await page.goto(job_url, timeout=30000)
                    await asyncio.sleep(3)

                    job_html = await page.content()
                    job_soup = BeautifulSoup(job_html, "html.parser")

                    title = job_soup.find("h1")
                    description = job_soup.find("div", class_="job-description")

                    jobs.append({
                        "id": job_url.split("/")[-1],
                        "title": title.get_text(strip=True) if title else "No Title Found",
                        "description": description.get_text(strip=True) if description else "No Description Found",
                        "link": job_url
                    })

                await asyncio.sleep(self.delay)
            await browser.close()
        return jobs

class ShuftiSession:
    def __init__(self, email, password):
        self.scraper = JobScraper(email, password)
        self.messaging_agent = MessagingAgent()