import os
import requests

from cachetools import cached, TTLCache


class OrderService:
    """This class provide order information"""

    # 1 hour cache time
    cache = TTLCache(maxsize=100, ttl=3600)

    @cached(cache)
    def get_order_information(self, order_id):
        url = 'https://api.konnektive.com/order/query/'
        payload = {'orderId': order_id,
                   'loginId': os.getenv('KONNEKTIVE_USER'),
                   'password': os.getenv('KONNEKTIVE_PASS')
                   }
        result = requests.post(url, params=payload)
        data = result.json()

        if data['result'] == 'ERROR':
            raise ValueError(data['message'])

        order = data['message']['data'][0]
        return order
