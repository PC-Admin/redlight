import logging
import hashlib
import json
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
        # URL where we'll check if the room/user combination is allowed.
        self._redlight_url = config.get("redlight_url", "http://127.0.0.1:8008/_matrix/loj/v1/abuse_lookup")
        self._agent = Agent(reactor)  # Twisted agent for making HTTP requests.

        logger.info("RedLightClientModule initialized.")
        logger.info(f"Redlight Server URL set to: {self._redlight_url}")

        # Register the user_may_join_room function to be called by Synapse before a user joins a room.
        api.register_spam_checker_callbacks(
            user_may_join_room=self.user_may_join_room
        )

    @staticmethod
    def double_hash_sha256(data: str) -> str:
        """Double-hash the data with SHA256 for added security."""
        first_hash = hashlib.sha256(data.encode()).digest()
        double_hashed = hashlib.sha256(first_hash).hexdigest()
        return double_hashed

    async def user_may_join_room(
        self, user: str, room: str, is_invited: bool
    ) -> Union["synapse.module_api.NOT_SPAM", "synapse.module_api.errors.Codes"]:

        logger.info(f"User {user} is attempting to join room {room}. Invitation status: {is_invited}.")

        # Double-hash the room and user IDs.
        hashed_room_id = self.double_hash_sha256(room)
        hashed_user_id = self.double_hash_sha256(user)

        # Prepare the HTTP body.
        body = _JsonProducer({
            "room_id_hash": hashed_room_id,
            "user_id_hash": hashed_user_id
        })

        # Make the HTTP request to our redlight server.
        response = await self._agent.request(
            b"PUT",
            self._redlight_url.encode(),
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
            logger.warn(f"User {user} not allowed to join room {room}.")
            raise AuthError(403, "User not allowed to join this room.")
        elif response.code == 204:
            logger.info(f"User {user} allowed to join room {room}.")
            return NOT_SPAM  # Allow the user to join.
        else:
            # Handle unexpected responses by logging them and allowing the user to join as a fallback.
            logger.error(f"Unexpected response code {response.code} with body: {response_body}")
            logger.warn(f"Defaulting to allowing user {user} to join due to unexpected response code.")
            return NOT_SPAM

# Function to parse the module's configuration.
def parse_config(config: dict) -> dict:
    return config

# Factory function to create an instance of the RedlightClientModule.
def create_module(api: ModuleApi, config: dict) -> RedlightClientModule:
    return RedlightClientModule(config, api)
