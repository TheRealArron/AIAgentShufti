from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time

def fill_and_submit_form(driver, form_data):
    """
    Fills out and submits a form using form_data.

    Args:
        driver (webdriver): Selenium WebDriver instance
        form_data (dict): Dictionary with keys like 'name', 'email', 'message'
    """
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    field_keywords = {
        'name': ['name', 'お名前', '氏名'],
        'email': ['email', 'メール'],
        'message': ['message', '自己紹介', '紹介文', '志望動機']
    }

    for input_tag in soup.find_all(['input', 'textarea']):
        input_type = input_tag.get('type', '').lower()
        input_name = input_tag.get('name', '').lower()
        placeholder = input_tag.get('placeholder', '').lower()
        aria_label = input_tag.get('aria-label', '').lower()
        label_text = ''

        if input_tag.has_attr('id'):
            label = soup.find('label', {'for': input_tag['id']})
            if label:
                label_text = label.text.strip().lower()

        text = f"{input_name} {placeholder} {aria_label} {label_text}"

        for key, keywords in field_keywords.items():
            if any(k in text for k in keywords) and key in form_data:
                try:
                    element = driver.find_element(By.NAME, input_tag.get('name')) \
                        if input_tag.get('name') else driver.find_element(By.XPATH, f"//*[@placeholder='{placeholder}']")
                    element.clear()
                    element.send_keys(form_data[key])
                    time.sleep(0.5)
                except Exception as e:
                    print(f"Could not fill {key}: {e}")

    # Find and click submit
    submit_keywords = ['submit', '送信', '応募']
    buttons = driver.find_elements(By.TAG_NAME, 'button') + driver.find_elements(By.TAG_NAME, 'input')

    for button in buttons:
        try:
            btn_text = button.text.lower()
            btn_val = button.get_attribute('value') or ''
            if any(word in btn_text or word in btn_val.lower() for word in submit_keywords):
                button.click()
                print("Form submitted.")
                return
        except Exception as e:
            print(f"Could not click submit: {e}")
