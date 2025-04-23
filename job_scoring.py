from transformers import T5ForConditionalGeneration, T5Tokenizer, MarianMTModel, MarianTokenizer
import torch

# ===== Translation Setup (Japanese → English) =====
JPN2ENG_MODEL = "Helsinki-NLP/opus-mt-ja-en"
jpn_tokenizer = MarianTokenizer.from_pretrained(JPN2ENG_MODEL)
jpn_model = MarianMTModel.from_pretrained(JPN2ENG_MODEL)

# Cache for previously translated texts
translation_cache = {}


def translate_to_english(text):
    """
    Translates Japanese text to English using MarianMT.
    Caches the result to avoid redundant translation.
    """
    if not text.strip():
        return ""

    if text in translation_cache:
        return translation_cache[text]

    try:
        batch = jpn_tokenizer([text], return_tensors="pt", truncation=True, padding=True)
        translated = jpn_model.generate(**batch)
        translated_text = jpn_tokenizer.decode(translated[0], skip_special_tokens=True)
        translation_cache[text] = translated_text  # Cache the result
        return translated_text
    except Exception as e:
        print(f"[ERROR] Translation failed: {e}")
        return text  # Fallback to original


# ===== Relevance Scoring Setup =====
SCORING_MODEL = "google/flan-t5-small"
tokenizer = T5Tokenizer.from_pretrained(SCORING_MODEL)
model = T5ForConditionalGeneration.from_pretrained(SCORING_MODEL)


def score_job_relevance(title, description, requirements, user_profile):
    """
    Computes a relevance score (0–10) between a job and a user profile.
    Uses a translation model to translate job details from Japanese to English before scoring.
    """
    title_en = translate_to_english(title)
    description_en = translate_to_english(description)
    requirements_en = translate_to_english(requirements)

    profile_text = (
        f"My name is {user_profile.get('name', 'Anonymous')}. "
        f"I have experience in {', '.join(user_profile.get('skills', []))}. "
        f"{user_profile.get('bio', '')}"
    )

    prompt = (
        f"Given the profile and job information, rate the relevance from 0 to 10:\n"
        f"Profile: {profile_text}\n"
        f"Job Title: {title_en}\n"
        f"Job Description: {description_en}\n"
        f"Job Requirements: {requirements_en}\n"
        f"Score:"
    )

    print("[DEBUG] Prompt for scoring model:\n", prompt)

    try:
        inputs = tokenizer(prompt, return_tensors="pt", truncation=True, padding=True).to(model.device)
        with torch.no_grad():
            # Set parameters for beam search to control diversity and quality of generated score
            outputs = model.generate(
                inputs["input_ids"],
                max_length=20,
                num_beams=5,
                no_repeat_ngram_size=2,
                temperature=0.7,  # Temperature controls randomness (lower is more deterministic)
                early_stopping=True
            )

        score_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        score = float(score_text.strip())

        # Ensure the score is in the range [0, 10]
        return max(0.0, min(10.0, score))

    except Exception as e:
        print(f"[ERROR] Scoring failed: {e}")
        return 0.0
