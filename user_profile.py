# user_profile.py
def get_user_profile(email, name, skills):
    """
    Returns a user profile based on the provided inputs from the GUI.

    Args:
        email (str): User's email address.
        name (str): User's name.
        skills (list): List of user skills.

    Returns:
        dict: User profile data.
    """
    return {
        "name": name,
        "email": email,
        "skills": skills,
        "bio": "User bio information not provided."  # Can be customized or left blank
    }
