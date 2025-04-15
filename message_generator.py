# message_generator.py
from transformers import T5ForConditionalGeneration, T5Tokenizer
import torch

# Load FLAN-T5 base model & tokenizer
model_name = "google/flan-t5-small"
tokenizer = T5Tokenizer.from_pretrained(model_name)
model = T5ForConditionalGeneration.from_pretrained(model_name)

def generate_application_message(job_title, job_description, job_requirements=None, user_profile=None):
    profile_text = f"My name is {user_profile['name']}. I have experience in {', '.join(user_profile['skills'])}. {user_profile['bio']}"

    prompt = f"""Write a polite, concise job application message in English using the following profile and job details.
Profile: {profile_text}
Job Title: {job_title}
Job Description: {job_description}
Job Requirements: {job_requirements or "None"}
"""

    # Print prompt length for debugging
    print(f"Prompt Length: {len(prompt)} characters")

    # Tokenize input with truncation if necessary
    input_ids = tokenizer(prompt, return_tensors="pt", max_length=1024, truncation=True).input_ids

    with torch.no_grad():
        # Generate a longer and richer response
        output_ids = model.generate(
            input_ids,
            max_length=400,
            num_beams=5,
            early_stopping=True,
            no_repeat_ngram_size=2,
        )

    message = tokenizer.decode(output_ids[0], skip_special_tokens=True)
    return message
