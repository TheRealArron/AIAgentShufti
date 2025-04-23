import asyncio
import json
import logging
from bs4 import BeautifulSoup
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from shufti_session import ShuftiSession
from message_generator import generate_application_message
from job_filter import is_relevant_job
from form_filler import fill_and_submit_form
from field_mapper import identify_field_and_fill
from job_scoring import score_job_relevance

APPLIED_JOBS_FILE = "applied_jobs.json"
LOG_FILE = "application_log.txt"

# Set up logging with log rotation
logging.basicConfig(level=logging.DEBUG, filename=LOG_FILE, filemode='a',
                    format='%(asctime)s - %(levelname)s - %(message)s')


def load_applied_jobs():
    try:
        with open(APPLIED_JOBS_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_applied_jobs(applied_jobs):
    with open(APPLIED_JOBS_FILE, "w") as f:
        json.dump(applied_jobs, f)


def log_application_status(job_id, success):
    status = "successfully" if success else "failed"
    logging.info(f"Job {job_id} was {status} applied.")


def is_valid_profile(user_profile):
    required_fields = ["name", "email", "skills"]
    return all(field in user_profile and user_profile[field] for field in required_fields)


def initialize_webdriver():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # headless mode
    return webdriver.Chrome(ChromeDriverManager().install(), options=options)


def extract_form_data(driver, user_profile):
    form_data = {}
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    for label in soup.find_all("label"):
        label_text = label.get_text(strip=True)
        placeholder = label.find_next("input") or label.find_next("textarea")
        placeholder_text = placeholder.get("placeholder") if placeholder else None
        value = identify_field_and_fill(label_text, placeholder_text, user_data=user_profile)

        if value:
            sanitized_label = label_text.lower().replace(" ", "_")
            form_data[sanitized_label] = value

    return form_data


def attempt_form_submission(job_url, user_profile):
    if not is_valid_profile(user_profile):
        logging.error("[ERROR] Invalid user profile provided to form submission.")
        return

    try:
        driver = initialize_webdriver()
        driver.get(job_url)

        form_data = extract_form_data(driver, user_profile)

        if not form_data:
            logging.error("[ERROR] Failed to extract form data.")
            return

        fill_and_submit_form(driver, form_data)
        logging.info("[FORM FILLED] Form filled and submitted.")
    except Exception as e:
        logging.error(f"Form submission failed for {job_url}: {e}")
    finally:
        driver.quit()


class AIJobAgent:
    def __init__(self, user_session, user_name="Your AI Agent", user_email=None, user_skills=None,
                 user_bio="No bio provided."):
        self.session = user_session
        self.user_name = user_name
        self.user_email = user_email
        self.user_skills = user_skills or []
        self.user_bio = user_bio
        self.user_profile = {
            "name": self.user_name,
            "email": self.user_email,
            "skills": self.user_skills,
            "bio": self.user_bio
        }
        self.applied_jobs = load_applied_jobs()

    async def process_job(self, job, log_callback):
        job_id = job.get("id")
        if not job_id or job_id in self.applied_jobs:
            return

        logging.debug(f"[DEBUG] Job data: {job}")

        # Score relevance
        score = score_job_relevance(
            job["title"],
            job["description"],
            job.get("requirements", ""),
            user_profile=self.user_profile
        )

        log_callback(f"[RELEVANCE SCORE] Job {job_id} scored {score:.2f}\n")

        if not is_relevant_job(job, self.user_profile):
            log_callback(f"[SKIPPED] Job {job_id} deemed irrelevant.\n")
            return

        # Form-based application detection
        if any(kw in job["description"].lower() for kw in ["fill out", "application form", "submit your info"]):
            logging.debug(f"[DEBUG] Attempting form submission for {job_id}")
            attempt_form_submission(job["link"], self.user_profile)
            log_callback(f"[FORM SUBMITTED] Job {job_id}\n")
            self.applied_jobs.append(job_id)
            save_applied_jobs(self.applied_jobs)
            return

        # Message-based application
        message = generate_application_message(
            job["title"],
            job["description"],
            job.get("requirements", ""),
            user_profile=self.user_profile
        )

        success = self.session.messaging_agent.send_message(job_id, message)
        if success:
            self.applied_jobs.append(job_id)
            save_applied_jobs(self.applied_jobs)
            log_callback(f"[SUCCESS] Applied to job {job_id}\n")
        else:
            log_callback(f"[FAILURE] Failed to apply to job {job_id}\n")
        log_application_status(job_id, success)

    async def run(self, log_callback):
        jobs = await self.session.scraper.crawl_jobs(user_profile=self.user_profile)

        tasks = []
        for job in jobs:
            tasks.append(self.process_job(job, log_callback))

        await asyncio.gather(*tasks)


async def run_agent_with_name(email, password, name, skills, bio, log_callback=print):
    user_profile = {
        "name": name,
        "email": email,
        "skills": skills,
        "bio": bio
    }
    session = ShuftiSession(email, password, user_name=name, user_profile=user_profile)
    agent = AIJobAgent(session, user_name=name, user_email=email, user_skills=skills, user_bio=bio)
    await agent.run(log_callback)

