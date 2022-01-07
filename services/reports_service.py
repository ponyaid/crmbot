import os
import requests

from cachetools import cached, TTLCache


class ReportsService:
    """This class provide order information"""

    # 1 hour cache time
    cache = TTLCache(maxsize=100, ttl=3600)

    @cached(cache)
    def get_mid_summary_report(self, start_date=''):
        url = 'https://api.konnektive.com/reports/mid-summary/'
        payload = {
            'loginId': os.getenv('KONNEKTIVE_USER'),
            'password': os.getenv('KONNEKTIVE_PASS')
        }
        if start_date:
            payload['startDate'] = start_date
            payload['endDate'] = ''

        result = requests.post(url, params=payload)
        data = result.json()

        if data['result'] == 'ERROR':
            raise ValueError(data['message'])

        order = data['message']['data']
        return order
