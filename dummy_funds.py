import json


def get_funds(criteria: dict = None) -> str:
    """Retrieve funds based on given criteria"""
    database = [
        {
            'name': 'Global Growth Fund', 
            'ticker': 'GLGFX',
            'category': 'Global Large-Stock Growth', 
            'morningstar_rating': 4,
            'risk_level': 'Moderate',
            'total_return_ytd': 15.72,
            'expense_ratio': 0.85,
            'minimum_investment': 250000
        },
        {
            'name': 'US Large Cap Value Fund', 
            'ticker': 'USLVX',
            'category': 'Large Value', 
            'morningstar_rating': 5,
            'risk_level': 'Low',
            'total_return_ytd': 9.34,
            'expense_ratio': 0.68,
            'minimum_investment': 2500
        },
        {
            'name': 'Emerging Markets Bond Fund', 
            'ticker': 'EMBFX',
            'category': 'Emerging Markets Bond', 
            'morningstar_rating': 3,
            'risk_level': 'High',
            'total_return_ytd': 6.21,
            'expense_ratio': 0.95,
            'minimum_investment': 10000
        },
        {
            'name': 'Technology Sector Fund', 
            'ticker': 'TECHX',
            'category': 'Technology', 
            'morningstar_rating': 4,
            'risk_level': 'High',
            'total_return_ytd': 22.51,
            'expense_ratio': 1.05,
            'minimum_investment': 5000
        },
        {
            'name': 'Sustainable Energy Fund', 
            'ticker': 'SUENX',
            'category': 'Alternative Energy', 
            'morningstar_rating': 5,
            'risk_level': 'Moderate',
            'total_return_ytd': 18.63,
            'expense_ratio': 1.15,
            'minimum_investment': 1000
        }
    ]

    if criteria:
        filtered_funds = database
        if 'risk_level' in criteria:
            filtered_funds = [fund for fund in filtered_funds if fund['risk_level'] == criteria['risk_level']]
        if 'min_rating' in criteria:
            filtered_funds = [fund for fund in filtered_funds if fund['morningstar_rating'] >= criteria['min_rating']]
        if 'max_expense_ratio' in criteria:
            filtered_funds = [fund for fund in filtered_funds if fund['expense_ratio'] <= criteria['max_expense_ratio']]
        if 'max_investment' in criteria:
            filtered_funds = [fund for fund in filtered_funds if fund['minimum_investment'] <= criteria['max_investment']]
        return json.dumps(filtered_funds)
    else:
        return json.dumps(database)