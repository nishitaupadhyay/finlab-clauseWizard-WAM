from typing import List, Dict, Any

def get_clients(city: str = None) -> List[Dict[str, Any]]:
    database = {
        "Boston": [
            {'name': 'Lawrence Summers', 'age': 55, 'profession': 'Professor', 'affiliation': 'Harvard University', 'active_tiaa_member': True, 'invested_assets': 180000, 'last_contacted_days': 15, 'details': 'Lawrence appears to be 10 years from retirement and is estimated to have $40k in investable assets that are not invested in TIAA. Lawrence has been with TIAA for over three years an favors an aggressive risk profile and passive management. Of the assets with TIAA, they appear to draw from a broad array of fund managers, including both TIAA-affiliated and outside funds.'},
            {'name': 'Peter Galison', 'age': 64, 'profession': 'Professor', 'affiliation': 'Harvard University', 'active_tiaa_member': True, 'invested_assets': 130000, 'last_contacted_days': 20, 'details': 'Peter has been with TIAA for two years and he favors a conservative strategy that maximizes long term profits while avoiding risk.'},
            {'name': 'Eric Maskin', 'age': 35, 'profession': 'Professor', 'affiliation': 'Boston University', 'active_tiaa_member': True, 'invested_assets': 200000, 'last_contacted_days': 10, 'details': ''},
            {'name': 'Catherine Dulac', 'age': 42, 'profession': 'Professor', 'affiliation': 'Boston College', 'active_tiaa_member': False, 'invested_assets': 0, 'last_contacted_days': 0, 'details': ''},
            {'name': 'Gary King', 'age': 62, 'profession': 'Professor', 'affiliation': 'MIT', 'active_tiaa_member': True, 'invested_assets': 80000, 'last_contacted_days': 50, 'details': ''},
        ],
        "Chicago": [
            {'name': 'John Doe', 'age': 55, 'profession': 'Professor', 'affiliation': 'Harvard University', 'active_tiaa_member': True, 'invested_assets': 180000, 'last_contacted_days': 15, 'details': ''},
        ],
    }

    try:
        if city:
            return database.get(city, [])
    except Exception as e:
        print("Error fetching client data", str(e))
        return []
