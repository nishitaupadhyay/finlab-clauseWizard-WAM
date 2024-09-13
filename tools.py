from typing import List, Dict, Any

def get_clients(city: str = None) -> List[Dict[str, Any]]:
    print(f"Fetching clients from {city}...")
    database = {
        "Boston": [
            {'name': 'Lawrence Summers', 'email':'client@example.com', 'age': 55, 'profession': 'Professor', 'affiliation': 'Harvard University',  'invested_assets': 180000, 'last_contacted_days': 15, 'details': 'Lawrence appears to be 10 years from retirement and is estimated to have $40k in investable assets that are not invested in TIAA. Lawrence has been with TIAA for over three years an favors an aggressive risk profile and passive management. Of the assets with TIAA, they appear to draw from a broad array of fund managers, including both TIAA-affiliated and outside funds.'},
            {'name': 'Peter Galison', 'email':'Lawrence@example.com','age': 64, 'profession': 'Professor', 'affiliation': 'Harvard University', 'invested_assets': 130000, 'last_contacted_days': 20, 'details': 'Peter has been with TIAA for two years and he favors a conservative strategy that maximizes long term profits while avoiding risk.'},
            {'name': 'Eric Maskin', 'email':'Lawrence@example.com', 'age': 35, 'profession': 'Professor', 'affiliation': 'Boston University',  'invested_assets': 200000, 'last_contacted_days': 10, 'details': ''},
            {'name': 'Catherine Dulac', 'email':'Lawrence@example.com','age': 42, 'profession': 'Professor', 'affiliation': 'Boston College', 'invested_assets': 0, 'last_contacted_days': 0, 'details': ''},
            {'name': 'Gary King','email':'Lawrence@example.com', 'age': 62, 'profession': 'Professor', 'affiliation': 'MIT', 'invested_assets': 80000, 'last_contacted_days': 50, 'details': ''},
        ],
        "Chicago": [
            {'name': 'John Doe', 'email':'Lawrence@example.com','age': 55, 'profession': 'Professor', 'affiliation': 'Harvard University', 'active_tiaa_member': True, 'invested_assets': 180000, 'last_contacted_days': 15, 'details': ''},
        ],
    }

    try:
        if city:
            print("Fetching clients from", database.get(city, []))
            return database.get(city, [])
    except Exception as e:
        print("Error fetching client data", str(e))
        return []
