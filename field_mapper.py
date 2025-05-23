from transformers import T5Tokenizer, T5ForConditionalGeneration
import torch
import json
from user_profile import get_user_profile

# Load tokenizer and model once (you can move this outside the function to avoid reloading repeatedly)
tokenizer = T5Tokenizer.from_pretrained("google/flan-t5-small")
model = T5ForConditionalGeneration.from_pretrained("google/flan-t5-small")

def identify_field_and_fill(label_text, placeholder_text=None, surrounding_text=None, user_data=None):
    if user_data is None:
        print("[ERROR] User data is required.")
        return None

    # Ensure that 'bio' is part of the user profile (it should be if passed correctly from the agent)
    bio = user_data.get('bio', 'No bio provided.')

    # Construct the prompt to include the user's bio
    prompt = f"""
You are a form-filling assistant. You will receive label and placeholder text from a web form field.
Based on the meaning, choose the most suitable value from this user's profile:

USER PROFILE:
{json.dumps(user_data, indent=2)}

Now, analyze the field below and return ONLY the value from the profile that should be filled:

Label: {label_text}
Placeholder: {placeholder_text or 'None'}
Surrounding Text: {surrounding_text or 'None'}

If you can't determine it, reply with "UNKNOWN".
"""

    # Tokenize and generate response
    input_ids = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512).input_ids
    outputs = model.generate(input_ids, max_length=50, do_sample=False)
    result = tokenizer.decode(outputs[0], skip_special_tokens=True).strip()

    # If model returns "UNKNOWN", return None
    return None if result.upper() == "UNKNOWN" else result

def extract_form_data(labels, user_profile):
    """
    Extract and map form data using the user's profile based on labels and placeholders.

    :param labels: List of labels (strings) to map the values to
    :param user_profile: Dictionary containing the user's profile
    :return: Dictionary containing the field values to be filled in the form
    """
    form_data = {}

    for label in labels:
        # Attempt to identify the corresponding value for each field
        value = identify_field_and_fill(label, user_data=user_profile)
        if value:
            form_data[label] = value
        else:
            print(f"[WARNING] No value found for label: {label}")

    return form_data

# Example usage (assuming user_profile is passed):
# user_profile = get_user_profile()
# labels = ["Name", "Email", "Bio"]
# form_data = extract_form_data(labels, user_profile)
