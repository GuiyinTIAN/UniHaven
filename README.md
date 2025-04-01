# UniHaven
UniHaven is a web service designed to help non-local students at the University of Hong Kong (HKU) and other universities find suitable off-campus rental accommodation.



# UniHaven - API Documentation

UniHaven 是一个为非本地学生提供校外住宿解决方案的 Django 项目。以下是所有 API 和页面的调用方式。

---

## 目录
1. [首页](#首页)
2. [地址查找 API](#地址查找-api)
3. [添加住宿](#添加住宿)
4. [查看住宿列表](#查看住宿列表)
5. [搜索住宿](#搜索住宿)
6. [查看住宿详情](#查看住宿详情)
7. [预订住宿](#预订住宿)
8. [取消预订](#取消预订)

---

### 首页

**URL**: `/`  
**方法**: `GET`  
**说明**: 显示项目的首页，提供导航到搜索住宿和添加住宿的功能。

#### 示例
```bash
curl -X GET "http://127.0.0.1:8000/"
```

---

### 地址查找 API

**URL**: `/lookup-address/`  
**方法**: `GET`  
**说明**: 根据地址查询香港政府 API，返回地址的详细信息。

#### 参数
- `address` (必填): 要查询的地址。

#### 示例
```bash
curl -X GET "http://127.0.0.1:8000/lookup-address/?address=HKU"
```

#### 响应示例
```json
{
    "EnglishAddress": {
        "BuildingName": "HKU SCHOOL OF PROFESSIONAL AND CONTINUING EDUCATION",
        "EstateName": "",
        "StreetName": "WAH LAM PATH",
        "BuildingNo": "3",
        "District": "SOUTHERN DISTRICT",
        "Region": "HK"
    },
    "ChineseAddress": {
        "BuildingName": "香港大學專業進修學院",
        "EstateName": "",
        "StreetName": "華林徑",
        "BuildingNo": "3",
        "District": "南區",
        "Region": "香港"
    },
    "GeospatialInformation": {
        "Latitude": "22.25221",
        "Longitude": "114.13809",
        "Northing": "812604",
        "Easting": "832270",
        "GeoAddress": "3228612615T20050430"
    }
}
```

---

### 添加住宿

**URL**: `/add-accommodation/`  
**方法**: `POST`  
**说明**: 添加新的住宿信息。

#### 参数
| 参数名           | 类型     | 描述                                   |
|------------------|----------|----------------------------------------|
| `title`          | 字符串   | 住宿标题，例如 "New Apartment"         |
| `description`    | 字符串   | 住宿描述，例如 "A cozy apartment near HKU." |
| `type`           | 字符串   | 住宿类型，例如 "APARTMENT"、"HOUSE" 或 "HOSTEL" |
| `beds`           | 整数     | 床位数量，例如 `2`                     |
| `bedrooms`       | 整数     | 卧室数量，例如 `1`                     |
| `price`          | 浮点数   | 价格（以港币为单位），例如 `4500`      |
| `address`        | 字符串   | 地址，例如 "123 Main Street"           |
| `available_from` | 日期     | 可用开始日期，例如 "2025-04-01"        |
| `available_to`   | 日期     | 可用结束日期，例如 "2025-12-31"        |

#### 示例
```bash
curl -X POST "http://127.0.0.1:8000/add-accommodation/" \
     -H "Accept: application/json" \
     -H "Content-Type: application/json" \
     -d '{
         "title": "Apartment1",
         "description": "A cozy apartment near HKU.",
         "type": "APARTMENT",
         "beds": 2,
         "bedrooms": 1,
         "price": 4500,
         "address": "HKU",
         "available_from": "2025-04-01",
         "available_to": "2025-12-31"
     }'
```

#### 响应示例
```json
{
    "success": true,
    "message": "Accommodation added successfully!"
}
```

---

### 查看住宿列表

**URL**: `/list-accommodation/`  
**方法**: `GET`  
**说明**: 获取所有住宿的列表。

#### 示例
```bash
curl -X GET "http://127.0.0.1:8000/list-accommodation/" -H "Accept: application/json"
```

#### 响应示例
```json
{
    "accommodations": [
        {
            "id": 1,
            "title": "Cozy Apartment",
            "description": "A nice apartment near HKU.",
            "type": "APARTMENT",
            "price": 4500,
            "beds": 2,
            "bedrooms": 1,
            "available_from": "2025-04-01",
            "available_to": "2025-12-31",
            "region": "HK"
        }
    ]
}
```

---

### 搜索住宿

**URL**: `/search-accommodation/`  
**方法**: `GET`  
**说明**: 根据条件搜索住宿。

#### 参数
| 参数名           | 描述                                   |
|------------------|----------------------------------------|
| `type`           | 住宿类型，例如 "APARTMENT"、"HOUSE" 或 "HOSTEL" |
| `region`         | 地区，例如 "HK"、"KL" 或 "NT"         |
| `available_from` | 可用开始日期，例如 "2025-04-01"        |
| `available_to`   | 可用结束日期，例如 "2025-12-31"        |
| `min_beds`       | 最小床位数，例如 `2`                  |
| `min_bedrooms`   | 最小卧室数，例如 `1`                  |
| `max_price`      | 最大价格，例如 `5000`                 |

#### 示例
```bash
curl -X GET "http://127.0.0.1:8000/search-accommodation/?type=APARTMENT&region=HK&min_beds=2&max_price=5000" -H "Accept: application/json"
```

---

### 查看住宿详情

**URL**: `/accommodation/<id>/`  
**方法**: `GET`  
**说明**: 获取特定住宿的详细信息。

#### 示例
```bash
curl -X GET "http://127.0.0.1:8000/accommodation/1/" -H "Accept: application/json"
```

#### 响应示例
```json
{
    "id": 1,
    "title": "Cozy Apartment",
    "description": "A nice apartment near HKU.",
    "type": "APARTMENT",
    "price": 4500,
    "beds": 2,
    "bedrooms": 1,
    "available_from": "2025-04-01",
    "available_to": "2025-12-31",
    "region": "HK",
    "reserved": false,
    "formatted_address": "123 Main Street, Central, HK"
}
```

---

### 预订住宿

**URL**: `/reserve_accommodation/<id>/`  
**方法**: `POST`  
**说明**: 预订指定的住宿。

#### 示例
```bash
curl -X POST "http://127.0.0.1:8000/reserve_accommodation/1/" \
     -H "Content-Type: application/json"
```

#### 响应示例
```json
{
    "success": true,
    "message": "Accommodation 'Cozy Apartment' has been reserved."
}
```

---

### 取消预订

**URL**: `/cancel_reservation/<id>/`  
**方法**: `POST`  
**说明**: 取消指定的住宿预订。

#### 示例
```bash
curl -X POST "http://127.0.0.1:8000/cancel_reservation/1/" \
     -H "Content-Type: application/json"
```

#### 响应示例
```json
{
    "success": true,
    "message": "Reservation for accommodation 'Cozy Apartment' has been canceled."
}
```

---

## 注意事项

1. **CSRF Token**:
   - 如果启用了 CSRF 验证，请确保在请求中包含 `X-CSRFToken` 头部和 `csrftoken` Cookie。
   - 示例：
     ```bash
     curl -b cookies.txt -X POST "http://127.0.0.1:8000/add-accommodation/" \
          -H "Content-Type: application/json" \
          -H "X-CSRFToken: <your-csrf-token>" \
          -d '{...}'
     ```

2. **日期格式**:
   - 所有日期参数必须为 `YYYY-MM-DD` 格式。

3. **错误处理**:
   - 如果请求失败，API 会返回适当的错误消息和状态码。

通过以上说明，您可以轻松调用 UniHaven 项目的所有功能。