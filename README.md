# UniHaven - Student Accommodation Solutions

UniHaven is a Django-based project designed to provide off-campus accommodation solutions for non-local students. Below is the documentation for all APIs and pages.

---

## Table of Contents
1. [Home](#home)
2. [Address Lookup API](#address-lookup-api)
3. [Add Accommodation](#add-accommodation)
4. [View Accommodation List](#view-accommodation-list)
5. [Search Accommodation](#search-accommodation)
6. [View Accommodation Details](#view-accommodation-details)
7. [Reserve Accommodation](#reserve-accommodation)
8. [Cancel Reservation](#cancel-reservation)

---

### Home

**URL**: `/`  
**Method**: `GET`  
**Description**: Displays the homepage with navigation options to search for accommodations or add new accommodations.

#### Example
```bash
curl -X GET "http://127.0.0.1:8000/"
```

---

### Address Lookup API

**URL**: `/lookup-address/`  
**Method**: `GET`  
**Description**: Queries the Hong Kong government API to retrieve detailed address information.

#### Parameters
- `address` (required): The address to query.

#### Example
```bash
curl -X GET "http://127.0.0.1:8000/lookup-address/?address=Main%20Street"
```

#### Response Example
```json
{
    "EnglishAddress": {
        "BuildingName": "Main Building",
        "EstateName": "Main Estate",
        "StreetName": "Main Street",
        "BuildingNo": "123",
        "District": "Central",
        "Region": "HK"
    },
    "ChineseAddress": {
        "BuildingName": "主楼",
        "EstateName": "主屋苑",
        "StreetName": "主街",
        "BuildingNo": "123",
        "District": "中环",
        "Region": "香港"
    },
    "GeospatialInformation": {
        "Latitude": 22.3964,
        "Longitude": 114.1095,
        "Northing": 123456,
        "Easting": 654321,
        "GeoAddress": "123 Main Street, Central, HK"
    }
}
```

---

### Add Accommodation

**URL**: `/add-accommodation/`  
**Method**: `POST`  
**Description**: Adds a new accommodation listing.

#### Parameters
| Parameter         | Type     | Description                              |
|-------------------|----------|------------------------------------------|
| `title`           | String   | Accommodation title, e.g., "New Apartment" |
| `description`     | String   | Description of the accommodation         |
| `type`            | String   | Type of accommodation, e.g., "APARTMENT", "HOUSE", or "HOSTEL" |
| `beds`            | Integer  | Number of beds                           |
| `bedrooms`        | Integer  | Number of bedrooms                       |
| `price`           | Float    | Price in HKD                             |
| `address`         | String   | Address of the accommodation             |
| `available_from`  | Date     | Start date of availability               |
| `available_to`    | Date     | End date of availability                 |

#### Example
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
         "available_to": "2025-12-31"
     }'
```

#### Response Example
```json
{
    "success": true,
    "message": "Accommodation added successfully!"
}
```

---

### View Accommodation List

**URL**: `/list-accommodation/`  
**Method**: `GET`  
**Description**: Retrieves a list of all accommodations with optional filters.

#### Parameters
| Parameter          | Description                                   |
|--------------------|-----------------------------------------------|
| `type`             | Type of accommodation, e.g., "APARTMENT", "HOUSE", or "HOSTEL" |
| `region`           | Region, e.g., "HK", "KL", or "NT"            |
| `available_from`   | Start date of availability                   |
| `available_to`     | End date of availability                     |
| `min_beds`         | Minimum number of beds                       |
| `min_bedrooms`     | Minimum number of bedrooms                   |
| `max_price`        | Maximum price in HKD                         |
| `distance`         | Maximum distance from HKU (in kilometers)    |
| `order_by_distance`| Whether to sort by distance (`true` or `false`) |

#### Example
```bash
curl -X GET "http://127.0.0.1:8000/list-accommodation/?type=APARTMENT&distance=5&order_by_distance=true" -H "Accept: application/json"
```

#### Response Example
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
            "region": "HK",
            "distance": 3.2
        }
    ]
}
```

---

### Search Accommodation

**URL**: `/search-accommodation/`  
**Method**: `GET`  
**Description**: Searches for accommodations based on specified criteria.

#### Example
```bash
curl -X GET "http://127.0.0.1:8000/search-accommodation/?type=House&region=HK&distance=10" -H "Accept: application/json"
```

---

### View Accommodation Details

**URL**: `/accommodation/<id>/`  
**Method**: `GET`  
**Description**: Retrieves detailed information about a specific accommodation.

#### Example
```bash
curl -X GET "http://127.0.0.1:8000/accommodation/1/" -H "Accept: application/json"
```

#### Response Example
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

### Reserve Accommodation

**URL**: `/reserve_accommodation/<id>/`  
**Method**: `POST`  
**Description**: Reserves a specific accommodation.

#### Example
```bash
curl -X POST "http://127.0.0.1:8000/reserve_accommodation/1/" \
     -H "Content-Type: application/json" \
     --cookie "user_identifier=123e4567-e89b-12d3-a456-426614174000"
```

#### Response Example
```json
{
    "success": true,
    "message": "Accommodation 'Cozy Apartment' has been reserved."
}
```

---

### Cancel Reservation

**URL**: `/cancel_reservation/<id>/`  
**Method**: `POST`  
**Description**: Cancels the reservation for a specific accommodation.

#### Example
```bash
curl -X POST "http://127.0.0.1:8000/cancel_reservation/1/" \
     -H "Content-Type: application/json" \
     --cookie "user_identifier=123e4567-e89b-12d3-a456-426614174000"
```

#### Response Example
```json
{
    "success": true,
    "message": "Reservation for accommodation 'Cozy Apartment' has been canceled."
}
```

---

## Notes

1. **CSRF Token**:
   - If CSRF protection is enabled, ensure that the `X-CSRFToken` header and `csrftoken` cookie are included in the request.
   - Example:
     ```bash
     curl -b cookies.txt -X POST "http://127.0.0.1:8000/add-accommodation/" \
          -H "Content-Type: application/json" \
          -H "X-CSRFToken: <your-csrf-token>" \
          -d '{...}'
     ```

2. **Date Format**:
   - All date parameters must follow the `YYYY-MM-DD` format.

3. **Distance Calculation**:
   - Distances are calculated based on the coordinates of HKU (latitude: 22.28143, longitude: 114.14006).

4. **Error Handling**:
   - If a request fails, the API will return an appropriate error message and status code.

With this documentation, you can easily interact with all the features of the UniHaven project. 