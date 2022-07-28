import json
import logging
import threading

import requests
from homeassistant.util.dt import now

API_URL = "https://api.64clouds.com/v1/getLiveServiceInfo?"


def query_bwh(veid, api_key):
    query_url = API_URL + 'veid=' + veid + '&api_key=' + api_key
    response = requests.get(query_url)
    logging.debug(f"query url: {query_url}, response: {response.text}")
    json_obj = json.loads(response.text)
    return json_obj


class BWH:

    def __init__(self, veid, api_key):
        self._state = None
        self._state_time = None
        self._veid = veid
        self._api_key = api_key
        self._lock = threading.Lock()

    def update(self):
        with self._lock:
            now_time = now()
            # 5分钟一次
            if self._state_time is None or (now_time - self._state_time).seconds > 180:
                logging.info("query bwh for data...")
                state = query_bwh(self._veid, self._api_key)
                self._state = state
                self._state_time = now_time
            else:
                logging.debug(f"last date update time is {self._state_time}")

    @property
    def used_bandwidth(self):
        self.update()
        return round(float(self._state['data_counter']) / 1024 / 1024 / 1024, 2)

    @property
    def monthly_bandwidth(self):
        self.update()
        return round(float(self._state['plan_monthly_data']) / 1024 / 1024 / 1024, 2)

    @property
    def state(self):
        self.update()
        return self._state['ve_status']

    @property
    def disk_used(self):
        self.update()
        return round(float(self._state['ve_used_disk_space_b']) / 1024 / 1024 / 1024, 2)
