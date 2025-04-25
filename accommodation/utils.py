from .models import University

def get_university_from_user_id(user_id):
    """
    根据用户ID判断所属大学
    
    Args:
        user_id (str): 用户ID，例如 "HKU_123456" 或 "HKUST_789123"
        
    Returns:
        University: 用户所属大学对象，如果找不到则返回None
    """
    if not user_id:
        return None
        
    # 获取所有大学的代码
    university_codes = list(University.objects.values_list('code', flat=True))
    
    # 检查用户ID是否以任何大学代码开头
    for code in university_codes:
        if user_id.upper().startswith(code.upper() + "_"):
            return University.objects.get(code=code)
    
    # 如果没有匹配项，尝试找HKU作为默认值
    try:
        return University.objects.get(code='HKU')
    except University.DoesNotExist:
        return None
