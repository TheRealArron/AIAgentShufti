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
from job_scoring import score_job_relevance  # Optional logging

APPLICATION_TEMPLATE = """
Hello {client_name},

I am very interested in the position of {job_title}. I am confident I can complete this task efficiently using my AI Agent. Let's discuss further!

Best regards,
{user_name}
"""

APPLIED_JOBS_FILE = "applied_jobs.json"
LOG_FILE = "application_log.txt"

# Set up logging
logging.basicConfig(level=logging.DEBUG, filename=LOG_FILE, filemode='a', format='%(asctime)s - %(levelname)s - %(message)s')

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

def attempt_form_submission(job_url, user_profile):
    if not user_profile or not isinstance(user_profile, dict):
        logging.error("[ERROR] Invalid user profile provided to form submission.")
        return

    try:
        driver = webdriver.Chrome(ChromeDriverManager().install())
        driver.get(job_url)

        form_data = {
            "name": user_profile["name"],
            "email": user_profile.get("email", ""),
            "message": "Hello, I’m interested in this opportunity."
        }

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        for label in soup.find_all("label"):
            try:
                label_text = label.get_text(strip=True)
                placeholder = label.find_next("input") or label.find_next("textarea")
                placeholder_text = placeholder.get("placeholder") if placeholder else None

                value = identify_field_and_fill(label_text, placeholder_text, user_data=user_profile)

                if value:
                    # Sanitize label text to avoid issues with invalid dictionary keys
                    sanitized_label = label_text.lower().replace(" ", "_")
                    form_data[sanitized_label] = value
                else:
                    logging.warning(f"No value identified for label '{label_text}'.")

            except Exception as e:
                logging.error(f"Failed processing form label: {e}")

        fill_and_submit_form(driver, form_data)
        logging.info("[FORM FILLED] Form filled and submitted.")
    except Exception as e:
        logging.error(f"Form submission failed for {job_url}: {e}")
    finally:
        driver.quit()

class AIJobAgent:
    def __init__(self, user_session, user_name="Your AI Agent", user_email=None, user_skills=None):
        self.session = user_session
        self.user_name = user_name
        self.user_email = user_email
        self.user_skills = user_skills or []
        self.applied_jobs = load_applied_jobs()

    async def run(self, log_callback):
        jobs = await self.session.scraper.crawl_jobs()
        for job in jobs:
            job_id = job.get("id")
            if not job_id or job_id in self.applied_jobs:
                continue

            # Log job data for debugging
            logging.debug(f"[DEBUG] Job data: {job}")

            # Optional: log relevance score
            score = score_job_relevance(job["title"], job["description"], job.get("requirements", ""))
            log_callback(f"[RELEVANCE SCORE] Job {job_id} scored {score:.2f}\n")

            if not is_relevant_job(job):
                log_callback(f"[SKIPPED] Job {job_id} deemed irrelevant.\n")
                continue

            # Better form detection
            if any(kw in job["description"].lower() for kw in ["fill out", "application form", "submit your info"]):
                user_profile = {
                    "name": self.user_name,
                    "email": self.user_email,
                    "skills": self.user_skills,
                }

                if not user_profile.get("name") or not user_profile.get("email") or not user_profile.get("skills"):
                    logging.error(f"[ERROR] Missing user profile details: {user_profile}")
                    continue

                logging.debug(f"[DEBUG] Received user_profile: {user_profile}")
                attempt_form_submission(job["link"], user_profile)
                log_callback(f"[FORM SUBMITTED] Job {job_id}\n")
                self.applied_jobs.append(job_id)
                save_applied_jobs(self.applied_jobs)
                continue

            # Message-based application
            message = generate_application_message(
                job["title"], job["description"], job.get("requirements", ""), user_profile={
                    "name": self.user_name,
                    "skills": self.user_skills,
                    "bio": "No bio provided."
                }
            )

            success = self.session.messaging_agent.send_message(job_id, message)
            if success:
                self.applied_jobs.append(job_id)
                save_applied_jobs(self.applied_jobs)
                log_callback(f"[SUCCESS] Applied to job {job_id}\n")
            else:
                log_callback(f"[FAILURE] Failed to apply to job {job_id}\n")
            log_application_status(job_id, success)

            # Add cooldown between jobs
            await asyncio.sleep(2)

async def run_agent_with_name(email, password, name, skills, log_callback=print):
    session = ShuftiSession(email, password, user_name=name)
    agent = AIJobAgent(session, user_name=name, user_email=email, user_skills=skills)
    await agent.run(log_callback)
