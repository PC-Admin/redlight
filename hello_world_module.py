import logging
from typing import Union
from synapse.module_api import ModuleApi

logger = logging.getLogger(__name__)

class HelloWorldModule:
    def __init__(self, config: dict, api: ModuleApi):
        self._api = api
        
        # Log a message to indicate the module's initialization
        logger.info("HelloWorldModule initialized.")
        
        # Register the spam checker callback
        api.register_spam_checker_callbacks(
            user_may_join_room=self.user_may_join_room
        )

    async def user_may_join_room(
        self, user: str, room: str, is_invited: bool
    ) -> Union["synapse.module_api.NOT_SPAM", "synapse.module_api.errors.Codes"]:
        
        # Log the event of a user trying to join a room
        logger.info(f"User {user} is attempting to join room {room}. Invitation status: {is_invited}.")
        
        # Log the desired message
        logger.info("Hello World!")
        
        # Return NOT_SPAM to allow the operation (joining the room)
        #return self._api.NOT_SPAM
        return self._api.errors.Codes.FORBIDDEN

def parse_config(config: dict) -> dict:
    return config

def create_module(api: ModuleApi, config: dict) -> HelloWorldModule:
    return HelloWorldModule(config, api)