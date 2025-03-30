import threading
import time

import requests


class SelfPingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.keep_running = True
        self.thread = threading.Thread(target=self.ping_self_periodically)
        self.thread.daemon = True
        self.thread.start()

    def ping_self_periodically(self):
        while self.keep_running:
            try:
                prod = "http://richtato.onrender.com"
                response = requests.get(prod)
                print(f"Pinged {prod} Status code: {response.status_code}")

                dev = "http://richtato-dev.onrender.com"
                response = requests.get(dev)
                print(f"Pinged {dev} Status code: {response.status_code}")

            except requests.RequestException as e:
                print(f"Failed to ping self: {e}")

            # Wait for 15 minutes (900 seconds) before pinging again
            time.sleep(10)

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def stop_pinging(self):
        """Stop the background thread."""
        self.keep_running = False
        if self.thread.is_alive():
            self.thread.join()
            self.thread.join()
