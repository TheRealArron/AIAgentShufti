from transformers import T5ForConditionalGeneration, T5Tokenizer, MarianMTModel, MarianTokenizer
import torch

# Translation Setup (Japanese → English)
jpn2eng_model_name = "Helsinki-NLP/opus-mt-ja-en"
jpn_tokenizer = MarianTokenizer.from_pretrained(jpn2eng_model_name)
jpn_model = MarianMTModel.from_pretrained(jpn2eng_model_name)

def translate_to_english(text):
    if not text.strip():
        return ""
    batch = jpn_tokenizer([text], return_tensors="pt", truncation=True, padding=True)
    translated = jpn_model.generate(**batch)
    return jpn_tokenizer.decode(translated[0], skip_special_tokens=True)


# ===== Relevance Scoring Setup =====
scoring_model_name = "google/flan-t5-small"
tokenizer = T5Tokenizer.from_pretrained(scoring_model_name)
model = T5ForConditionalGeneration.from_pretrained(scoring_model_name)

RELEVANCE_THRESHOLD = 5.0  # Adjust this as needed

def score_job_relevance(title, description, requirements, user_profile):
    # Translate all Japanese text to English
    title_en = translate_to_english(title)
    description_en = translate_to_english(description)
    requirements_en = translate_to_english(requirements)

    profile_text = f"My name is {user_profile.get('name', 'Anonymous')}. I have experience in {', '.join(user_profile.get('skills', []))}. {user_profile.get('bio', '')}"

    prompt = f"""Based on the following profile and job information, rate the relevance from 0 to 10:
Profile: {profile_text}
Job Title: {title_en}
Job Description: {description_en}
Job Requirements: {requirements_en}
Score:"""

    print("DEBUG PROMPT:", prompt)

    inputs = tokenizer(prompt, return_tensors="pt", truncation=True).to(model.device)

    with torch.no_grad():
        outputs = model.generate(inputs["input_ids"], max_length=20)

    score_text = tokenizer.decode(outputs[0], skip_special_tokens=True)

    try:
        score = float(score_text.strip())
        return max(0.0, min(10.0, score))  # Clamp between 0–10
    except:
        return 0.0


# ===== Relevance Filter Function =====
def is_relevant_job(job_data, user_profile):
    title = job_data.get("title", "")
    description = job_data.get("description", "")
    requirements = job_data.get("requirements", "")

    score = score_job_relevance(title, description, requirements, user_profile)
    print(f"[RELEVANCE SCORE] Job {job_data.get('job_id', 'N/A')} scored {score:.2f}")

    return score >= RELEVANCE_THRESHOLD
