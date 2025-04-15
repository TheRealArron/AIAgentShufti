from job_scoring import score_job_relevance

# Adjustable threshold (0 to 10)
RELEVANCE_THRESHOLD = 7.0

def is_relevant_job(job_data):
    """
    Checks if a job is relevant based on title, description, and requirements.
    """
    title = job_data.get("title", "")
    description = job_data.get("description", "")
    requirements = job_data.get("requirements", "")

    score = score_job_relevance(title, description, requirements)
    print(f"[Score: {score:.1f}] {title}")

    return score >= RELEVANCE_THRESHOLD
