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

logger = logging.getLogger(__name__)

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
        self._redlight_url = config.get("redlight_url", "https://duckdomain.xyz/_matrix/loj/v1/abuse_lookup")
        self._agent = Agent(reactor)

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

        body = _JsonProducer({
            "room_id_hash": hashed_room_id,
            "user_id_hash": hashed_user_id
        })

        response = await self._agent.request(
            b"PUT",
            self._redlight_url.encode(),
            Headers({'Content-Type': [b'application/json']}),
            body
        )

        response_body_bytes = await readBody(response)
        response_body = response_body_bytes.decode("utf-8")

        try:
            response_json = json.loads(response_body)
        except json.JSONDecodeError:
            logger.error(f"Failed to decode response body: {response_body}")
            #return NOT_SPAM  # default to allowing if there's an error

        if response.code == 200:
            raise AuthError(403, "User not allowed to join this room")
        elif response.code == 204:
            return NOT_SPAM
        else:
            logger.error(f"Unexpected response code {response.code} with body: {response_body}")
            return NOT_SPAM  # default to allowing if there's an unexpected response

def parse_config(config: dict) -> dict:
    return config

def create_module(api: ModuleApi, config: dict) -> RedlightClientModule:
    return RedlightClientModule(config, api)
