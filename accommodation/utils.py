from .models import University

def get_university_from_user_id(user_id):
    """
    Determine the affiliated university based on th
    
    Args:
        user_id (str): User ID，for example "HKU_123456" or "HKUST_789123" or "CUHK_456789"
        
    Returns:
        University: If the university object to which the user belongs cannot be found, return None
    """
    if not user_id:
        return None
        
    # Get all university codes from the database
    university_codes = list(University.objects.values_list('code', flat=True))
    
    # check if user_id starts with any of the university codes
    for code in university_codes:
        if user_id.upper().startswith(code.upper() + "_"):
            return University.objects.get(code=code)
    
    # if no match found, set default to HKU
    try:
        return University.objects.get(code='HKU')
    except University.DoesNotExist:
        return None
