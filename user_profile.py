def get_user_profile(email, name, skills, bio):
    """
    Returns a user profile based on the provided inputs from the GUI.

    Args:
        email (str): User's email address.
        name (str): User's name.
        skills (list): List of user skills.
        bio (str): User's bio information.

    Returns:
        dict: User profile data.
    """
    return {
        "name": name,
        "email": email,
        "skills": skills,
        "bio": bio  # Now passing the bio from GUI input
    }
