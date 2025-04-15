from transformers import T5ForConditionalGeneration, T5Tokenizer
import torch

model_name = "google/flan-t5-small"
tokenizer = T5Tokenizer.from_pretrained(model_name)
model = T5ForConditionalGeneration.from_pretrained(model_name)

def score_job_relevance(job_title, job_description, job_requirements, user_profile):
    if not user_profile or not isinstance(user_profile, dict):
        return 0.0

    profile_text = f"My skills are: {', '.join(user_profile.get('skills', []))}. My bio: {user_profile.get('bio', '')}"

    prompt = f"""Based on the following profile and job, rate the relevance from 0 to 10 (only output the number).

Profile: {profile_text}
Job Title: {job_title}
Job Description: {job_description}
Job Requirements: {job_requirements}
"""

    input_ids = tokenizer(prompt, return_tensors="pt", max_length=512, truncation=True).input_ids

    with torch.no_grad():
        output_ids = model.generate(input_ids, max_length=5, num_beams=5, early_stopping=True)

    score_str = tokenizer.decode(output_ids[0], skip_special_tokens=True).strip()

    try:
        return float(score_str)
    except ValueError:
        return 0.0
