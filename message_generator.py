# message_generator.py
from transformers import T5ForConditionalGeneration, T5Tokenizer
import torch

# Load model & tokenizer once
model_name = "google/flan-t5-small"
tokenizer = T5Tokenizer.from_pretrained(model_name)
model = T5ForConditionalGeneration.from_pretrained(model_name)

def generate_application_message(job_title, job_description, job_requirements=None, user_profile=None):
    if not user_profile:
        raise ValueError("User profile is required to generate application message.")

    name = user_profile.get("name", "An AI professional")
    skills = ', '.join(user_profile.get("skills", [])) or "various technologies"
    bio = user_profile.get("bio", "")

    prompt = f"""
You are an AI assistant writing a job application message.

USER PROFILE:
Name: {name}
Skills: {skills}
Bio: {bio}

JOB DETAILS:
Title: {job_title}
Description: {job_description}
Requirements: {job_requirements or "None"}

Write a concise and professional message to apply for the job.
"""

    # Debug prompt length
    print(f"[DEBUG] Prompt Length: {len(prompt)} characters")

    input_ids = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=1024).input_ids

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
