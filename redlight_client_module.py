import logging
import hashlib
import json
import asyncio
from typing import Union
from synapse.module_api import ModuleApi, NOT_SPAM
from synapse.api.errors import AuthError
from twisted.web.client import Agent, readBody
from twisted.web.http_headers import Headers
from twisted.web.iweb import IBodyProducer
from twisted.internet import reactor
from twisted.internet import defer
from twisted.web.iweb import IBodyProducer
from zope.interface import implementer
from redlight_alert_bot import RedlightAlertBot

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

# Define a custom producer to convert our JSON data for HTTP requests.
@implementer(IBodyProducer)
class _JsonProducer:
    def __init__(self, data):
        self._data = json.dumps(data).encode("utf-8")
        self.length = len(self._data)

    def startProducing(self, consumer):
        consumer.write(self._data)
        return defer.succeed(None)

    def pauseProducing(self):
        pass

    def stopProducing(self):
        pass

class RedlightClientModule:
    def __init__(self, config: dict, api: ModuleApi):
        self._api = api
        # Your homeserver's URL
        self._homeserver_url = "https://" + config.get("homeserver_url", "127.0.0.1:8008")
        # The API token of your redlight bot user
        self._redlight_alert_bot_token = config.get("redlight_alert_bot_token", "")
        # The alert room your redlight bot will post too
        self._redlight_alert_room = config.get("redlight_alert_room", "")
        # Redlight server endpoint, where we'll check if the room/user combination is allowed.
        self._redlight_endpoint = "https://" + config.get("redlight_server", "127.0.0.1:8008") + "/_matrix/loj/v1/abuse_lookup"
        # Redlight API token
        self._redlight_api_token = config.get("redlight_api_token", "")
        self._agent = Agent(reactor)  # Twisted agent for making HTTP requests.

        # Create an instance of the RedlightAlertBot
        self.bot = RedlightAlertBot(self._homeserver_url, self._redlight_alert_bot_token)  # Adjust the homeserver and token as required

        logger.info("RedLightClientModule initialized.")
        logger.info(f"Redlight bot user token: {self._redlight_alert_bot_token}")
        logger.info(f"Redlight alert room: {self._redlight_alert_room}")
        logger.info(f"Redlight server endpoint set to: {self._redlight_endpoint}")

        # Register the user_may_join_room function to be called by Synapse before a user joins a room.
        api.register_spam_checker_callbacks(
            user_may_join_room=self.user_may_join_room
        )

    @staticmethod
    def hash_blake2(data: str) -> str:
        """Hash the data with BLAKE2 for upstream comparison."""
        room_id_hash = hashlib.blake2b(data.encode(), digest_size=32).hexdigest()  # Use hexdigest() instead of digest()
        return room_id_hash

    async def user_may_join_room(
        self, user: str, room: str, is_invited: bool
    ) -> Union["synapse.module_api.NOT_SPAM", "synapse.module_api.errors.Codes"]:

        logger.info(f"User {user} is attempting to join room {room}. Invitation status: {is_invited}.")

        # Double-hash the room and user IDs.
        hashed_room_id = self.hash_blake2(room)
        hashed_user_id = self.hash_blake2(user)

        # Prepare the HTTP body.
        body = _JsonProducer({
            "room_id_hash": hashed_room_id,
            "user_id_hash": hashed_user_id,
            "api_token": self._redlight_api_token
        })

        # Make the HTTP request to our redlight server.
        response = await self._agent.request(
            b"PUT",
            self._redlight_endpoint.encode(),
            Headers({'Content-Type': [b'application/json']}),
            body
        )

        # Extract the response body.
        response_body_bytes = await readBody(response)
        response_body = response_body_bytes.decode("utf-8")

        # Log the response content
        logger.info(f"Received response with code {response.code}. Content: {response_body}")

        try:
            # Try to parse the response body as JSON.
            response_json = json.loads(response_body)
        except json.JSONDecodeError:
            logger.error(f"Failed to decode response body: {response_body}")

        # Handle the response based on its HTTP status code.
        if response.code == 200:
            logger.warn(f"User {user} not allowed to join restricted room. report_id: {response_json['report_id']} room_id: {room}.")
            # Create the alert message
            alert_message = f"WARNING: Incident detected! User {user} was attempting to access a restricted room. report_id: {response_json['report_id']}, For the room id please check your redlight logs."
            # Start the synchronous send_alert_message method in a thread but don't await it
            loop = asyncio.get_event_loop()
            loop.run_in_executor(None, self.bot.send_alert_message, self._redlight_alert_room, alert_message)
            # Throw a 403 error that the user will see
            raise AuthError(403, "PERMISSION DENIED - This room violates server policy.")
        elif response.code == 204:
            logger.info(f"User {user} allowed to join room {room}.")
            return NOT_SPAM  # Allow the user to join.
        else:
            alert_message = f"Unexpected response code {response.code} with body {response_body}. Defaulting to allowing user {user} to join due to unexpected response code."
            # Handle unexpected responses by alerting and logging them, and allowing the user to join as a fallback.
            logger.error(alert_message)
            loop = asyncio.get_event_loop()
            loop.run_in_executor(None, self.bot.send_alert_message, self._redlight_alert_room, alert_message)
            return NOT_SPAM

# Function to parse the module's configuration.
def parse_config(config: dict) -> dict:
    return config

# Factory function to create an instance of the RedlightClientModule.
def create_module(api: ModuleApi, config: dict) -> RedlightClientModule:
    return RedlightClientModule(config, api)
