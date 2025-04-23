from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
import time

# ====== Keywords for Field Matching ======
FIELD_KEYWORDS = {
    'name': ['name', 'お名前', '氏名'],
    'email': ['email', 'メール'],
    'message': ['message', '自己紹介', '紹介文', '志望動機'],
    'bio': ['bio', '自己紹介', 'プロフィール']
}

SUBMIT_KEYWORDS = ['submit', '送信', '応募']


def get_label_text(soup, input_tag):
    """
    Extracts label text associated with an input field, if any.
    """
    if input_tag.has_attr('id'):
        label = soup.find('label', {'for': input_tag['id']})
        if label:
            return label.text.strip().lower()
    return ''


def find_input_element(driver, input_tag, placeholder):
    """
    Tries to find a Selenium element from a BeautifulSoup input tag.
    """
    try:
        if input_tag.get('name'):
            return driver.find_element(By.NAME, input_tag.get('name'))
        elif placeholder:
            return driver.find_element(By.XPATH, f"//*[@placeholder='{placeholder}']")
    except Exception as e:
        print(f"[WARN] Could not find input element: {e}")
    return None


def fill_and_submit_form(driver, form_data):
    """
    Fills out and submits a web form based on matching keywords.

    Args:
        driver: Selenium WebDriver instance
        form_data: Dictionary with fields like 'name', 'email', 'message', 'bio'
    """
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    for input_tag in soup.find_all(['input', 'textarea']):
        input_type = input_tag.get('type', '').lower()
        input_name = input_tag.get('name', '').lower()
        placeholder = input_tag.get('placeholder', '').lower()
        aria_label = input_tag.get('aria-label', '').lower()
        label_text = get_label_text(soup, input_tag)

        combined_text = f"{input_name} {placeholder} {aria_label} {label_text}"

        for key, keywords in FIELD_KEYWORDS.items():
            if key in form_data and any(k in combined_text for k in keywords):
                element = find_input_element(driver, input_tag, placeholder)
                if element:
                    try:
                        element.clear()
                        element.send_keys(form_data[key])
                        time.sleep(0.5)
                    except Exception as e:
                        print(f"[ERROR] Could not fill {key}: {e}")

    submit_buttons = driver.find_elements(By.TAG_NAME, 'button') + driver.find_elements(By.TAG_NAME, 'input')

    for button in submit_buttons:
        try:
            btn_text = button.text.lower()
            btn_value = (button.get_attribute('value') or '').lower()
            if any(k in btn_text or k in btn_value for k in SUBMIT_KEYWORDS):
                button.click()
                print("[INFO] Form submitted.")
                return
        except Exception as e:
            print(f"[ERROR] Could not click submit: {e}")
