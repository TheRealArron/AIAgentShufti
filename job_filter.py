from job_scoring import score_job_relevance

# Threshold for determining job relevance (scale: 0 to 10)
RELEVANCE_THRESHOLD = 5.0

# Translation cache to avoid repeated work
job_translation_cache = {}

def get_translated_job_data(job_data):
    """
    Retrieves translated job data (title, description, requirements).
    Uses caching to avoid redundant operations.

    Args:
        job_data (dict): Dictionary containing job information.

    Returns:
        dict: Translated job data with keys 'title', 'description', 'requirements'.
    """
    job_id = job_data.get('job_id', 'N/A')
    if job_id in job_translation_cache:
        return job_translation_cache[job_id]

    title = job_data.get("title", "")
    description = job_data.get("description", "")
    requirements = job_data.get("requirements", "")

    translated_data = {
        'title': title,
        'description': description,
        'requirements': requirements
    }

    # Cache the translated result
    job_translation_cache[job_id] = translated_data
    return translated_data

def is_relevant_job(job_data, user_profile):
    """
    Determines if a job is relevant to the user profile using a scoring function.

    Args:
        job_data (dict): Job information (title, description, requirements).
        user_profile (dict): User profile containing at least 'name' and 'skills'.

    Returns:
        bool: True if the job is relevant, False otherwise.
    """
    if not user_profile.get('name') or not user_profile.get('skills'):
        print(f"[SKIP] Missing name or skills in user profile.")
        return False

    translated_data = get_translated_job_data(job_data)
    title = translated_data['title']
    description = translated_data['description']
    requirements = translated_data['requirements']

    if not (title or description or requirements):
        print(f"[SKIP] Incomplete job data for job ID: {job_data.get('job_id', 'N/A')}")
        return False

    # Score relevance
    score = score_job_relevance(title, description, requirements, user_profile)
    print(f"[RELEVANCE SCORE] Job ID {job_data.get('job_id', 'N/A')}: {score:.2f}")

    return score >= RELEVANCE_THRESHOLD
