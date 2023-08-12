import logging
import hashlib
import json
import http.client
from typing import Union
from synapse.module_api import ModuleApi
from synapse.api.errors import AuthError
from twisted.internet import defer
from twisted.web.client import Agent, readBody
from twisted.web.http_headers import Headers

logger = logging.getLogger(__name__)

class RedlightClientModule:
    def __init__(self, config: dict, api: ModuleApi):
        self._api = api
        self._redlight_url = config.get("redlight_url", "https://duckdomain.xyz/_matrix/loj/v1/abuse_lookup")

        logger.info("RedLightClientModule initialized.")

        api.register_spam_checker_callbacks(
            user_may_join_room=self.user_may_join_room
        )

    @staticmethod
    def double_hash_sha256(data: str) -> str:
        first_hash = hashlib.sha256(data.encode()).digest()
        double_hashed = hashlib.sha256(first_hash).hexdigest()
        return double_hashed

    async def user_may_join_room(
        self, user: str, room: str, is_invited: bool
    ) -> Union["synapse.module_api.NOT_SPAM", "synapse.module_api.errors.Codes"]:

        logger.info(f"User {user} is attempting to join room {room}. Invitation status: {is_invited}.")

        hashed_room_id = self.double_hash_sha256(room)
        hashed_user_id = self.double_hash_sha256(user)

        # Send the PUT request
        connection = http.client.HTTPSConnection("localhost:8008")
        headers = {
            "Content-Type": "application/json"
        }
        body = json.dumps({
            "room_id_hash": hashed_room_id,
            "user_id_hash": hashed_user_id
        })
        connection.request("PUT", "/_matrix/loj/v1/abuse_lookup", body, headers)
        response = connection.getresponse()
        response_body = response.read()

        # Process the response from the server
        result = json.loads(response_body.decode())
        #logger.info(f'response.status = {response.status} and result["error"] = {result["error"]}')
        if response.status == 200:
            # Raise an AuthError if the API returns OK 200
            raise AuthError(403, "User not allowed to join this room")
        else:
            # Allow joining if no issue detected
            return self._api.NOT_SPAM

def parse_config(config: dict) -> dict:
    return config

def create_module(api: ModuleApi, config: dict) -> RedlightClientModule:
    return RedlightClientModule(config, api)
