import logging
import json
from synapse.module_api import ModuleApi
from twisted.web import http
from twisted.internet import defer
from twisted.internet.defer import inlineCallbacks
from twisted.web.server import NOT_DONE_YET
from twisted.web.http import OK, NO_CONTENT

# Define a handler and set its level and format
file_handler = logging.FileHandler('/var/log/matrix-synapse/redlight.log')
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# Get your logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)

# Ensure that this logger's messages don't propagate to the root logger
logger.propagate = False

class RedlightServerModule:
    def __init__(self, config: dict, api: ModuleApi):
        self._api = api

        # Register the abuse_lookup endpoint
        api.register_web_resource(
            "/_matrix/loj/v1/abuse_lookup",
            RedlightServerResource(self)
        )

        logger.info("RedlightServerModule initialized.")

class RedlightServerResource:

    isLeaf = True

    def __init__(self, module):
        self._module = module

    def render(self, request):
        method = request.method.decode('ascii')
        handler = getattr(self, f"on_{method}", None)

        if handler:
            def _respond(result):
                request.write(result)
                request.finish()

            def _error(failure):
                logger.error(f"Error processing abuse lookup request: {failure}")
                request.setResponseCode(500)
                request.write(json.dumps({"error": "Internal Server Error"}).encode("utf-8"))
                request.finish()

            d = handler(request)
            d.addCallbacks(_respond, _error)
            return NOT_DONE_YET
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

            # Extract room_id_hash and user_id_hash from the content
            data = json.loads(content)
            room_id_hash = data["room_id_hash"]
            user_id_hash = data["user_id_hash"]

            # Check the room_id_hash against your list/database or hardcoded value
            is_abuse = room_id_hash == "ee180279a57f716e5801335a2914e228667f363e460ccabcc49e8fd879e1be4a"

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

def create_module(api: ModuleApi, config: dict) -> RedlightServerModule:
    return RedlightServerModule(config, api)
