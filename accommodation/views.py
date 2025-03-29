import requests
from django.http import JsonResponse

def lookup_address(request):
    # 获取用户输入的地址
    address = request.GET.get("address", "")
    if not address:
        return JsonResponse({"error": "Address parameter is required"}, status=400)
    number = 1
    # 调用 API
    api_url = f"https://www.als.gov.hk/lookup?q={address}&n={number}"
    headers = {"Accept": "application/json"} 

    try:
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()  

        # 打印 API 返回的内容以调试
        # print("API Response:", response.text)

        # 尝试解析 JSON 响应
        try:
            data = response.json()
            return JsonResponse(data, safe=False)  # 返回 JSON 数据
        except ValueError:
            return JsonResponse({"error": "Invalid JSON response from API"}, status=500)

    except requests.HTTPError as e:
        # print error message for debugging
        print(f"HTTP Error: {e.response.status_code} - {e.response.text}")
        return JsonResponse({"error": f"HTTP Error: {e.response.status_code}"}, status=e.response.status_code)
    except requests.RequestException as e:
        return JsonResponse({"error": str(e)}, status=500)
