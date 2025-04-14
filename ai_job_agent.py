# ai_job_agent.py
import asyncio
import json
from shufti_session import ShuftiSession

APPLICATION_TEMPLATE = """
Hello {client_name},

I am very interested in the position of {job_title}. I am confident I can complete this task efficiently using my AI Agent. Let's discuss further!

Best regards,
Your AI Agent
"""

APPLIED_JOBS_FILE = "applied_jobs.json"
LOG_FILE = "application_log.txt"


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
    with open(LOG_FILE, "a") as f:
        status = "successfully" if success else "failed"
        f.write(f"Job {job_id} was {status} applied.\n")


class AIJobAgent:
    def __init__(self, user_session, name="Your AI Agent"):
        self.session = user_session
        self.name = name
        self.applied_jobs = load_applied_jobs()

    async def run(self, log_callback):
        jobs = await self.session.scraper.crawl_jobs()
        for job in jobs:
            job_id = job.get("id")
            if not job_id or job_id in self.applied_jobs:
                continue

            message = APPLICATION_TEMPLATE.format(
                job_title=job["title"],
                client_name=job.get("client_name", "there")
            )

            success = self.session.messaging_agent.send_message(job_id, message)
            if success:
                self.applied_jobs.append(job_id)
                save_applied_jobs(self.applied_jobs)
                log_callback(f"[SUCCESS] Applied to job {job_id}\n")
            else:
                log_callback(f"[FAILURE] Failed to apply to job {job_id}\n")
            log_application_status(job_id, success)


async def run_agent_with_name(email, password, name, log_callback=print):
    session = ShuftiSession(email, password)
    agent = AIJobAgent(session, name=name)
    await agent.run(log_callback)