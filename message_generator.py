from transformers import T5ForConditionalGeneration, T5Tokenizer
import torch

model_name = "google/flan-t5-small"
tokenizer = T5Tokenizer.from_pretrained(model_name)
model = T5ForConditionalGeneration.from_pretrained(model_name)

def generate_application_message(job_title, job_description, job_requirements, user_profile):
    if not user_profile or not isinstance(user_profile, dict):
        return "Hello, I’m interested in this job. Please let me know more."

    profile_text = f"My name is {user_profile.get('name', 'Anonymous')}. I have experience in {', '.join(user_profile.get('skills', []))}. {user_profile.get('bio', '')}"

    prompt = f"""Write a polite, concise job application message in English using the following profile and job details.
Profile: {profile_text}
Job Title: {job_title}
Job Description: {job_description}
Job Requirements: {job_requirements}
"""

    input_ids = tokenizer(prompt, return_tensors="pt", max_length=1024, truncation=True).input_ids

    with torch.no_grad():
        output_ids = model.generate(
            input_ids,
            max_length=400,
            num_beams=5,
            early_stopping=True,
            no_repeat_ngram_size=2,
        )

    message = tokenizer.decode(output_ids[0], skip_special_tokens=True)
    return message
