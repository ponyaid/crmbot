import os
import requests

from cachetools import cached, TTLCache


class CustomerService:
    """This class provide customer information"""

    # 1 hour cache time
    cache = TTLCache(maxsize=100, ttl=3600)

    @cached(cache)
    def get_customer_history(self, customer_id):
        url = 'https://api.konnektive.com/customer/history/'
        payload = {'customerId': customer_id,
                   'loginId': os.getenv('KONNEKTIVE_USER'),
                   'password': os.getenv('KONNEKTIVE_PASS'),
                   'resultsPerPage': 50
                   }
        result = requests.post(url, params=payload)
        data = result.json()

        if not data['message']['totalResults']:
            raise ValueError(
                'No customers matching those parameters could be found')

        history = data['message']['data']
        return history
