<h1 align="center">UniHaven - Student Accommodation Solutions</h1>

<div align="center">
  <img src="https://img.shields.io/badge/Django-4.x-green?style=flat-square&logo=django" alt="Django">
  <img src="https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python" alt="Python">
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=flat-square" alt="License">
</div>

> A professional Django-based platform for off-campus accommodation, tailored for non-local students in Hong Kong.

---

## Project Overview

**UniHaven** is an open-source Django project designed to help non-local students find, book, and manage off-campus accommodation in Hong Kong. The platform supports multi-criteria search, address lookup, online booking, reviews, and admin management.

---

## Tech Stack

- **Backend**: Django 4.x, SQLite3
- **Frontend**: HTML5, CSS3, Bootstrap (optional)
- **API**: RESTful, supports JSON/HTML
- **Deployment**: Local & Cloud supported

---

## Table of Contents
1. [Features](#features)
2. [Quick Start](#quick-start)
3. [API Reference](#api-reference)
4. [Contributing](#contributing)
5. [Deployment](#deployment)
6. [Contact](#contact)

---

## Features

- Multi-criteria accommodation search & filter
- Smart address lookup & map location
- Accommodation details & online booking
- Booking management & cancellation
- Accommodation reviews & ratings
- Admin backend management

---

## Quick Start

1. **Clone the repo**
    ```bash
    git clone <your-repo-url>
    cd UniHaven
    ```
2. **Install dependencies**
    ```bash
    pip install -r requirements.txt
    ```
3. **Migrate database**
    ```bash
    python manage.py migrate
    ```
4. **Run server**
    ```bash
    python manage.py runserver
    ```

---

## API Reference

See below for detailed API usage and examples.

---

...existing code...

---

## Contributing

We welcome all contributions! Please read [CONTRIBUTING.md] or contact the maintainer before submitting a PR, reporting a bug, or suggesting a feature.

---

## Deployment

1. For local development, follow the Quick Start steps.
2. For production, we recommend Gunicorn + Nginx, or deploying to cloud platforms (Heroku, Vercel, Alibaba Cloud, etc.).
3. Configure database, cache, and email services as needed.

---

## Contact

- Email: [your-email@example.com]
- Issues: Please use GitHub Issues for questions and suggestions.

---

### Home

**URL**: `/api/`  
**Method**: `GET`  
**Header**: `-H "Accept:application/json"` (for JSON response)  
**Description**: Displays the homepage with navigation options to search for accommodations or add new accommodations.

#### Example
```bash
curl -X GET "http://127.0.0.1:8000/api/" -H "Accept: application/json"
```
```json
{
    "message": "Welcome to UniHaven!"
}
```
---

### Address Lookup API

**URL**: `/api/lookup-address/`  
**Method**: `GET`  
**Description**: Queries the Hong Kong government API to retrieve detailed address information.

#### Parameters
- `address` (required): The address to query.

#### Example
```bash
curl -X GET "http://127.0.0.1:8000/api/lookup-address/?address=HKU"
```

#### Response Example
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

### Add Accommodation

**URL**: `/api/add-accommodation/`  
**Method**: `POST`  
**Header**: `-H "Content-Type:application/json"`  
**Header**: `-H "X-CSRFToken: <your-csrf-token>"` (optional, CSRF protection is enabled in development)  
**Description**: Adds a new accommodation listing.

#### Parameters
| Parameter         | Type     | Description                              |
|-------------------|----------|------------------------------------------|
| `title`           | String   | Accommodation title, e.g., "New Apartment" |
| `description`     | String   | Description of the accommodation         |
| `type`            | String   | Type of accommodation: "APARTMENT", "HOUSE", or "HOSTEL" |
| `beds`            | Integer  | Number of beds                           |
| `bedrooms`        | Integer  | Number of bedrooms                       |
| `price`           | Float    | Price in HKD                             |
| `address`         | String   | Address of the accommodation             |
| `available_from`  | Date     | Start date of availability (YYYY-MM-DD)  |
| `available_to`    | Date     | End date of availability (YYYY-MM-DD)    |
| `contact_phone`   | String   | Contact phone number                     |
| `contact_email`   | String   | Contact email address                    |

#### Example
```bash
curl -X POST "http://127.0.0.1:8000/api/add-accommodation/" \
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

#### Response Example
```json
{
    "success": true,
    "message": "Accommodation added successfully!"
}
```

---

### View Accommodation List

**URL**: `/api/list-accommodation/`  
**Method**: `GET`  
**Description**: Retrieves a list of all accommodations with optional filters.

#### Parameters
| Parameter          | Description                                   |
|--------------------|-----------------------------------------------|
| `type`             | Type of accommodation: "APARTMENT", "HOUSE", or "HOSTEL" |
| `region`           | Region: "HK" (Hong Kong Island), "KL" (Kowloon), or "NT" (New Territories) |
| `available_from`   | Start date of availability (YYYY-MM-DD)       |
| `available_to`     | End date of availability (YYYY-MM-DD)         |
| `min_beds`         | Minimum number of beds                        |
| `min_bedrooms`     | Minimum number of bedrooms                    |
| `max_price`        | Maximum price in HKD                          |
| `distance`         | Maximum distance from HKU (in kilometers)     |
| `order_by_distance`| Sort by distance: "true" or "false"           |
| `format`           | Response format, set to "json" for JSON format |

#### Example
```bash
curl -X GET "http://127.0.0.1:8000/api/list-accommodation/?type=APARTMENT&max_price=8000&distance=3&order_by_distance=true" -H "Accept: application/json"
```

#### Response Example
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

### Search Accommodation

**URL**: `/api/search-accommodation/`  
**Method**: `GET`  
**Header**: `-H "Accept:application/json"` or parameter `format=json`  
**Description**: Searches for accommodations based on specified criteria (redirects to list_accommodation).

#### Example
```bash
curl -X GET "http://127.0.0.1:8000/api/search-accommodation/?type=HOUSE&region=HK&distance=10" -H "Accept: application/json"
```

Or using format parameter:

```bash
curl -X GET "http://127.0.0.1:8000/api/search-accommodation/?type=HOUSE&region=HK&distance=10&format=json"
```

---

### View Accommodation Details

**URL**: `/api/accommodation_detail/<id>/`  
**Method**: `GET`  
**Header**: `-H "Accept: application/json"` (for JSON response)  
**Description**: Retrieves detailed information about a specific accommodation.

#### Example
```bash
curl -X GET "http://127.0.0.1:8000/api/accommodation_detail/1/" -H "Accept: application/json"
```

#### Response Example
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

### Reserve Accommodation

**URL**: `/api/reserve_accommodation/`  
**Method**: `POST`  
**Parameter**: `id` - Accommodation ID  
**Description**: Reserves a specific accommodation. Requires user_identifier cookie.

#### Example
```bash
curl -X POST "http://127.0.0.1:8000/api/reserve_accommodation/?id=1" \
     -H "Content-Type: application/json" \
     -b "user_identifier=student123"
```

#### Response Example
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

### Cancel Reservation

**URL**: `/api/cancel_reservation/`  
**Method**: `POST`  
**Parameter**: `id` - Accommodation ID  
**Description**: Cancels the reservation for a specific accommodation. Requires user_identifier cookie.

#### Example
```bash
curl -X POST "http://127.0.0.1:8000/api/cancel_reservation/?id=1" \
     -H "Content-Type: application/json" \
     -b "user_identifier=student123"
```

#### Response Example
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

### Delete Accommodation

**URL**: `/api/delete-accommodation/`  
**Method**: `POST`  
**Parameter**: `id` - Accommodation ID  
**Description**: Deletes a specific accommodation.

#### Example
```bash
curl -X POST "http://127.0.0.1:8000/api/delete-accommodation/?id=1" \
     -H "Content-Type: application/json"
```

#### Response Example
```json
{
    "success": true,
    "message": "Accommodation 'Cozy Apartment' has been deleted."
}
```

---

### Rate Accommodation

**URL**: `/api/rate/<accommodation_id>/`  
**Method**: `POST`  
**Description**: Rates a specific accommodation.

#### Parameters
| Parameter         | Type     | Description                              |
|-------------------|----------|------------------------------------------|
| `accommodation_id`| Integer  | ID of the accommodation to rate          |
| `rating`          | Integer  | Rating value (e.g., 1-5)                 |
| `comment`         | String   | Review comment (optional)                |

#### Example
```bash
curl -X POST "http://127.0.0.1:8000/api/rate/1/" \
     -H "Content-Type: application/json" \
     -d '{
         "rating": 5,
         "comment": "Excellent place to stay!"
     }'
```

#### Response Example
```json
{
    "success": true,
    "message": "Thank you for rating this accommodation!"
}
```

---

## Notes

1. **CSRF Token**:
   - If CSRF protection is enabled, ensure that the `X-CSRFToken` header and `csrftoken` cookie are included in the request.
   - Example:
     ```bash
     curl -b cookies.txt -X POST "http://127.0.0.1:8000/api/add-accommodation/" \
          -H "Content-Type: application/json" \
          -H "X-CSRFToken: <your-csrf-token>" \
          -d '{...}'
     ```

2. **Date Format**:
   - All date parameters must follow the `YYYY-MM-DD` format.

3. **Distance Calculation**:
   - Distances are calculated using the Haversine formula based on the coordinates of HKU (latitude: 22.28143, longitude: 114.14006).

4. **Content Negotiation**:
   - Most endpoints support both HTML and JSON responses based on the Accept header or format parameter
   - Use `Accept: application/json` or `format=json` for API interactions

5. **User Identification**:
   - For reservation operations, a user identifier cookie must be present.
   - The system sends confirmation emails to both the user and housing administrator.

With this documentation, you can easily interact with all the features of the UniHaven project.