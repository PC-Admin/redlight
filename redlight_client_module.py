import logging
import hashlib
from typing import Union
from synapse.module_api import ModuleApi
from synapse.api.errors import AuthError

logger = logging.getLogger(__name__)

class RedlightClientModule:
    def __init__(self, config: dict, api: ModuleApi):
        self._api = api

        # Log a message to indicate the module's initialization
        logger.info("RedLightClientModule initialized.")

        # Register the spam checker callback
        api.register_spam_checker_callbacks(
            user_may_join_room=self.user_may_join_room
        )

    @staticmethod
    def double_hash_sha256(data: str) -> str:
        """
        Double hash the given data using SHA-256.

        Args:
            data (str): The data to hash.

        Returns:
            str: The double-hashed data in hexadecimal format.
        """
        first_hash = hashlib.sha256(data.encode()).digest()
        double_hashed = hashlib.sha256(first_hash).hexdigest()
        return double_hashed

    async def user_may_join_room(
        self, user: str, room: str, is_invited: bool
    ) -> Union["synapse.module_api.NOT_SPAM", "synapse.module_api.errors.Codes"]:

        # Log the event of a user trying to join a room
        logger.info(f"User {user} is attempting to join room {room}. Invitation status: {is_invited}.")

        # Here's how you can use the double hashing function:
        hashed_room_id = self.double_hash_sha256(room)
        logger.info(f"Double hashed room ID: {hashed_room_id}")

        # Double hash the username
        hashed_user_id = self.double_hash_sha256(user)
        logger.info(f"Double hashed user ID: {hashed_user_id}")

        # Log the desired message
        logger.info("Hello World!")

        # Raise an AuthError to indicate the operation is forbidden
        raise AuthError(403, "User not allowed to join this room")

        # If you wish to allow the operation at some point, you can return:
        # return self._api.NOT_SPAM

def parse_config(config: dict) -> dict:
    return config

def create_module(api: ModuleApi, config: dict) -> RedlightClientModule:
    return RedlightClientModule(config, api)