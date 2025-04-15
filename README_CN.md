# UniHaven - 学生住宿解决方案

UniHaven 是一个基于 Django 的项目，旨在为非本地学生提供校外住宿解决方案。以下是所有 API 和页面的调用方法文档。

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
**请求头**: `-H "Accept:application/json"`（显示 JSON 输出）  
**说明**: 显示首页，提供搜索住宿和添加新住宿的导航选项。

#### 示例
```bash
curl -X GET "http://127.0.0.1:8000/" -H "Accept: application/json"
```
```json
{
    "message": "Welcome to UniHaven!"
}
```
---

### 地址查找 API

**URL**: `/lookup-address/`  
**方法**: `GET`  
**说明**: 查询香港政府 API 以获取详细的地址信息。

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
**请求头**: `-H "Content-Type:application/json"`  
**请求头**: `-H "X-CSRFToken: <your X-CSRFToken>"` (可选，开发环境下启用了 CSRF 保护)  
**说明**: 添加新的住宿信息。

#### 参数
| 参数名           | 类型     | 描述                                   |
|------------------|----------|----------------------------------------|
| `title`          | 字符串   | 住宿标题，例如 "新公寓"                |
| `description`    | 字符串   | 住宿描述                               |
| `type`           | 字符串   | 住宿类型，例如 "APARTMENT"、"HOUSE" 或 "HOSTEL" |
| `beds`           | 整数     | 床位数量                               |
| `bedrooms`       | 整数     | 卧室数量                               |
| `price`          | 浮点数   | 价格（港币）                           |
| `address`        | 字符串   | 住宿地址                               |
| `available_from` | 日期     | 可用开始日期                           |
| `available_to`   | 日期     | 可用结束日期                           |
| `contact_phone`  | 字符串   | 联系电话                               |
| `contact_email`  | 字符串   | 联系邮箱                               |

#### 示例
```bash
curl -X POST "http://127.0.0.1:8000/add-accommodation/" \
     -H "Content-Type: application/json" \
     -d '{
         "title": "New Apartment",
         "description": "A cozy apartment near HKU.",
         "type": "APARTMENT",
         "beds": 2,
         "bedrooms": 1,
         "price": 4500,
         "address": "123 Main Street",
         "available_from": "2025-04-01",
         "available_to": "2025-12-31",
         "contact_phone": "+852 1234 5678",
         "contact_email": "owner@example.com"
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
**说明**: 获取带有可选筛选条件的所有住宿列表。

#### 参数
| 参数名             | 描述                                   |
|--------------------|----------------------------------------|
| `type`             | 住宿类型，例如 "APARTMENT"、"HOUSE" 或 "HOSTEL" |
| `region`           | 地区，例如 "HK"、"KL" 或 "NT"         |
| `available_from`   | 可用开始日期                           |
| `available_to`     | 可用结束日期                           |
| `min_beds`         | 最小床位数                             |
| `min_bedrooms`     | 最小卧室数                             |
| `max_price`        | 最大价格（港币）                       |
| `distance`         | 距离香港大学的最大距离（公里）         |
| `order_by_distance`| 是否按距离排序（`true` 或 `false`）    |
| `format`           | 返回格式，设置为 `json` 时返回JSON格式 |

#### 示例
```bash
curl -X GET "http://127.0.0.1:8000/list-accommodation/?type=APARTMENT&max_price=8000&format=json"
```

#### 响应示例
```json
{
    "accommodations": [
        {
            "id": 15,
            "title": "Apartment1",
            "building_name": "University Residence",
            "description": "A cozy apartment near HKU.",
            "type": "APARTMENT",
            "price": "6500.00",
            "beds": 2,
            "bedrooms": 1,
            "available_from": "2025-04-01",
            "available_to": "2025-12-31",
            "region": "HK",
            "distance": 1.25,
            "reserved": false,
            "contact_phone": "+852 1234 5678",
            "contact_email": "owner@example.com"
        }
    ]
}
```

---

### 搜索住宿

**URL**: `/search-accommodation/`  
**方法**: `GET`  
**请求头**: `-H "Accept:application/json"` 或参数 `format=json`  
**说明**: 根据指定条件搜索住宿。此接口将重定向到列表接口，传递相应的查询参数。

#### 示例
```bash
curl -X GET "http://127.0.0.1:8000/search-accommodation/?type=HOUSE&region=HK&distance=10" -H "Accept: application/json"
```

或者使用参数指定JSON格式:

```bash
curl -X GET "http://127.0.0.1:8000/search-accommodation/?type=HOUSE&region=HK&distance=10&format=json"
```

---

### 查看住宿详情

**URL**: `/accommodation/<id>/`  
**方法**: `GET`  
**请求头**: `-H "Accept: application/json"`  
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
    "price": "4500.00",
    "beds": 2,
    "bedrooms": 1,
    "available_from": "2025-04-01",
    "available_to": "2025-12-31",
    "region": "HK",
    "reserved": false,
    "formatted_address": "123 Main Street, Central, HK",
    "building_name": "Grand Heights",
    "userID": "",
    "contact_phone": "+852 1234 5678",
    "contact_email": "owner@example.com"
}
```

---

### 预订住宿

**URL**: `/reserve_accommodation/`  
**方法**: `POST`  
**参数**: `id` - 住宿ID  
**说明**: 预订指定的住宿。需要user_identifier cookie。

#### 示例
```bash
curl -X POST "http://127.0.0.1:8000/reserve_accommodation/?id=1" \
     -H "Content-Type: application/json" \
     -b "user_identifier=student123"
```

#### 响应示例
```json
{
    "success": true,
    "message": "Accommodation 'Cozy Apartment' has been reserved.",
    "UserID": "student123",
    "accommodation": {
        "id": 1,
        "title": "Cozy Apartment",
        "description": "A nice apartment near HKU.",
        "type": "APARTMENT",
        "price": "4500.00",
        "beds": 2,
        "bedrooms": 1,
        "available_from": "2025-04-01",
        "available_to": "2025-12-31",
        "region": "HK",
        "reserved": true,
        "formatted_address": "123 Main Street, Central, HK",
        "building_name": "Grand Heights",
        "userID": "student123"
    }
}
```

---

### 取消预订

**URL**: `/cancel_reservation/`  
**方法**: `POST`  
**参数**: `id` - 住宿ID  
**说明**: 取消特定住宿的预订。需要user_identifier cookie。

#### 示例
```bash
curl -X POST "http://127.0.0.1:8000/cancel_reservation/?id=1" \
     -H "Content-Type: application/json" \
     -b "user_identifier=student123"
```

#### 响应示例
```json
{
    "success": true,
    "message": "Reservation for accommodation 'Cozy Apartment' has been canceled.",
    "UserID": "student123",
    "accommodation": {
        "id": 1,
        "title": "Cozy Apartment",
        "description": "A nice apartment near HKU.",
        "type": "APARTMENT",
        "price": "4500.00",
        "beds": 2,
        "bedrooms": 1,
        "available_from": "2025-04-01",
        "available_to": "2025-12-31",
        "region": "HK",
        "reserved": false,
        "formatted_address": "123 Main Street, Central, HK",
        "building_name": "Grand Heights",
        "userID": ""
    }
}
```

---

## 注意事项

1. **CSRF Token**:
   - 如果启用了 CSRF 保护，请确保请求中包含 `X-CSRFToken` 头部和 `csrftoken` Cookie。
   - 示例：
     ```bash
     curl -b cookies.txt -X POST "http://127.0.0.1:8000/add-accommodation/" \
          -H "Content-Type: application/json" \
          -H "X-CSRFToken: <your-csrf-token>" \
          -d '{...}'
     ```

2. **日期格式**:
   - 所有日期参数必须遵循 `YYYY-MM-DD` 格式。

3. **距离计算**:
   - 距离基于香港大学的坐标计算（纬度：22.28143，经度：114.14006）。
   - 使用Haversine公式计算直线距离。

4. **内容协商**:
   - 大多数端点支持基于Accept头或format查询参数的内容协商
   - 使用 `Accept: application/json` 或 `format=json` 获取JSON响应

5. **用户标识**:
   - 预订和取消预订操作需要用户标识cookie（user_identifier）
   - 系统会向用户和住房管理员发送确认邮件

通过本文档，您可以轻松使用 UniHaven 项目的所有功能。