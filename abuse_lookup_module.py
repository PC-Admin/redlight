import logging
from synapse.module_api import ModuleApi
from twisted.web.http import OK, NO_CONTENT
import json
from twisted.web import http

logger = logging.getLogger(__name__)

class AbuseLookupModule:
    def __init__(self, config: dict, api: ModuleApi):
        self._api = api
        
        # Register the abuse_lookup endpoint
        api.register_web_resource(
            "/_matrix/loj/v1/abuse_lookup",
            AbuseLookupResource(self)
        )
        
        logger.info("AbuseLookupModule initialized.")

class AbuseLookupResource:
    def __init__(self, module):
        self._module = module

    async def on_PUT(self, request):
        # Extract body from the request
        body = await request.content.read()
        content = body.decode("utf-8")
        
        # Log the request to Synapse's log
        logger.info(f"Received abuse lookup request: {content}")

        # Extract room_id from the content (assuming the content is JSON and valid)
        try:
            data = json.loads(content)
            room_id = data["room_id"]
            
            # TODO: Check the room_id against your list/database
            # For now, we'll just simulate it
            is_abuse = room_id == "!OEedGOAXDBahPyWMSQ:example.com"

            if is_abuse:
                return (http.OK, json.dumps({
                    "error": None,
                    "report_id": "b973d82a-6932-4cad-ac9f-f647a3a9d204",
                }).encode("utf-8"))
            else:
                return (http.NO_CONTENT, b"")

        except Exception as e:
            logger.error(f"Error processing abuse lookup request: {e}")
            return (400, json.dumps({"error": "Bad Request"}).encode("utf-8"))

    def __getattr__(self, name):
        # This will handle other HTTP methods like GET, POST, etc.
        # and return a 405 Method Not Allowed
        return self.method_not_allowed

    def method_not_allowed(self, _):
        return (405, json.dumps({"error": "Method Not Allowed"}).encode("utf-8"))

def parse_config(config: dict) -> dict:
    return config

def create_module(api: ModuleApi, config: dict) -> AbuseLookupModule:
    return AbuseLookupModule(config, api)
