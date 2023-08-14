import logging
import requests

# Setting up logging:
file_handler = logging.FileHandler('/var/log/matrix-synapse/redlight.log')
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)

# Prevent logger's messages from propagating to the root logger.
logger.propagate = False

class RedlightAlertBot:
    def __init__(self, homeserver, access_token):
        self.homeserver = homeserver
        self.access_token = access_token
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

    def send_alert_message(self, room_id, message):
        endpoint = f"{self.homeserver}/_matrix/client/r0/rooms/{room_id}/send/m.room.message"
        payload = {
            "msgtype": "m.text",
            "body": message
        }
        response = requests.post(endpoint, headers=self.headers, json=payload)

        # Check if the request was successful
        if response.status_code == 200:
            logger.info("Alert message sent successfully!")
        else:
            logger.info(f"Failed to send alert message. Status code: {response.status_code}, Response: {response.text}")
