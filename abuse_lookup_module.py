import logging
from synapse.module_api import ModuleApi
from twisted.web.http import OK, NO_CONTENT
import json
from twisted.web import http
from twisted.internet import defer
from twisted.internet.defer import inlineCallbacks

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

    isLeaf = True

    def __init__(self, module):
        self._module = module

    def render(self, request):
        method = request.method.decode('ascii')
        handler = getattr(self, f"on_{method}", None)

        if handler:
            result = handler(request)
            return result if isinstance(result, bytes) else self.method_not_allowed(request)
        else:
            return self.method_not_allowed(request)

    @inlineCallbacks
    def on_PUT(self, request):
        try:
            # Extract body from the request
            body = yield request.content.read()
            content = body.decode("utf-8")
            
            # Log the request to Synapse's log
            logger.info(f"Received abuse lookup request: {content}")

            # Extract room_id from the content
            data = json.loads(content)
            room_id = data["room_id"]
            
            # TODO: Check the room_id against your list/database
            is_abuse = room_id == "!OEedGOAXDBahPyWMSQ:example.com"

            if is_abuse:
                request.setResponseCode(http.OK)
                defer.returnValue(json.dumps({
                    "error": None,
                    "report_id": "b973d82a-6932-4cad-ac9f-f647a3a9d204",
                }).encode("utf-8"))
            else:
                request.setResponseCode(http.NO_CONTENT)
                defer.returnValue(b"")

        except Exception as e:
            logger.error(f"Error processing abuse lookup request: {e}")
            request.setResponseCode(400)
            defer.returnValue(json.dumps({"error": "Bad Request"}).encode("utf-8"))


    def on_GET(self, request):
        return self.method_not_allowed(request)

    def on_POST(self, request):
        return self.method_not_allowed(request)

    # And similarly for other methods you want to block like DELETE, HEAD, etc.

    def method_not_allowed(self, request):
        request.setResponseCode(405)
        return json.dumps({"error": "Method Not Allowed"}).encode("utf-8")

def parse_config(config: dict) -> dict:
    return config

def create_module(api: ModuleApi, config: dict) -> AbuseLookupModule:
    return AbuseLookupModule(config, api)
