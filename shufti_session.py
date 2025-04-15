import asyncio
import torch
from transformers import T5ForConditionalGeneration, T5Tokenizer
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from job_scoring import score_job_relevance

BASE_URL = "https://app.shufti.jp/jobs/search"
LOGIN_URL = "https://app.shufti.jp/login"

# Load your model and tokenizer once
model_name = "google/flan-t5-small"
tokenizer = T5Tokenizer.from_pretrained(model_name)
model = T5ForConditionalGeneration.from_pretrained(model_name)


class MessagingAgent:
    def __init__(self, user_name="Your AI Agent", user_profile=None):
        self.user_name = user_name
        self.user_profile = user_profile

    def send_message(self, job_id, job_title, job_description, job_requirements):
        if not self.user_profile:
            print(f"Sending default message for Job {job_id}: {job_title} (from {self.user_name})")
            return True

        message = self.generate_application_message(job_title, job_description, job_requirements)
        print(f"Sending message for Job {job_id}: {message} (from {self.user_name})")
        return True

    def generate_application_message(self, job_title, job_description, job_requirements):
        profile_text = f"My name is {self.user_profile.get('name', 'Anonymous')}. " \
                       f"I have experience in {', '.join(self.user_profile.get('skills', []))}. " \
                       f"{self.user_profile.get('bio', '')}"

        prompt = f"""Write a polite, concise job application message in English using the following profile and job details.
Profile: {profile_text}
Job Title: {job_title}
Job Description: {job_description}
Job Requirements: {job_requirements}
"""

        input_ids = tokenizer(prompt, return_tensors="pt", max_length=1024, truncation=True).input_ids
        with torch.no_grad():
            output_ids = model.generate(input_ids, max_length=400, num_beams=5, early_stopping=True,
                                        no_repeat_ngram_size=2)

        return tokenizer.decode(output_ids[0], skip_special_tokens=True).strip()


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

    async def crawl_jobs(self, user_profile):
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
                    requirements = job_soup.find("div", class_="job-requirements")

                    job = {
                        "id": job_url.split("/")[-1],
                        "title": title.get_text(strip=True) if title else "No Title Found",
                        "description": description.get_text(strip=True) if description else "No Description Found",
                        "requirements": requirements.get_text(strip=True) if requirements else "No Requirements Found",
                        "link": job_url
                    }

                    score = score_job_relevance(
                        job["title"],
                        job["description"],
                        job["requirements"],
                        user_profile
                    )

                    print(f"[SCORE: {score:.2f}] {job['title']}")


                    jobs.append(job)

                await asyncio.sleep(self.delay)

            await browser.close()
        return jobs


class ShuftiSession:
    def __init__(self, email, password, user_name="Your AI Agent", user_profile=None):
        if user_profile is None:
            user_profile = {
                "name": user_name,
                "email": email,
                "skills": [],
                "bio": "User bio information not provided."
            }
        self.user_profile = user_profile
        self.scraper = JobScraper(email, password)
        self.messaging_agent = MessagingAgent(user_name, user_profile)

    async def process_jobs(self):
        jobs = await self.scraper.crawl_jobs(self.user_profile)
        for job in jobs:
            self.messaging_agent.send_message(
                job['id'],
                job['title'],
                job['description'],
                job['requirements']
            )
