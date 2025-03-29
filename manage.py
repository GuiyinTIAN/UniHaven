#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
import json
import requests


def main():
    """Run administrative tasks."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "UniHaven.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


def get_address_info(query):
    url = f"https://www.als.gov.hk/lookup?q={query}"
    
    # Add custom headers
    headers = {
        'Accept': 'application/json',  # specify accepted response format
    }

    response = requests.get(url, headers=headers)

    #print("Status Code:", response.status_code)
    #print("Response Content:", response.text)  

    if response.status_code == 200:
        try:
            data = response.json()
            return extract_address_info(data)
        except json.JSONDecodeError:
            print("Error: Response is not in JSON format")
            return None
    else:
        print("Error fetching data from API:", response.status_code)
        return None

def extract_address_info(json_data):
    try:
        first_suggestion = json_data.get("SuggestedAddress", [])[0].get("Address", {}).get("PremisesAddress", {})
        chi_premises = first_suggestion.get("ChiPremisesAddress", {})
        geospatial = first_suggestion.get("GeospatialInformation", {})
        
        estate_name = chi_premises.get("ChiEstate", {}).get("EstateName", "N/A")
        latitude = geospatial.get("Latitude", "N/A")
        longitude = geospatial.get("Longitude", "N/A")
        
        return {
            "EstateName": estate_name,
            "Latitude": latitude,
            "Longitude": longitude
        }
    except IndexError:
        print("Error: No valid address found.")
        return None




if __name__ == "__main__":
    main()
    
    query = "香港大學"
    result = get_address_info(query)

    if result:
        print(json.dumps(result, indent=4, ensure_ascii=False))
