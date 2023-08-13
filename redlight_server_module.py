import logging
import json
from synapse.module_api import ModuleApi
from twisted.web import http
from twisted.internet import defer
from twisted.internet.defer import inlineCallbacks
from twisted.web.server import NOT_DONE_YET
from twisted.web.http import OK, NO_CONTENT

# Setting up logging specifically for this module:
# 1. Create a file handler to write logs to a specific file.
file_handler = logging.FileHandler('/var/log/matrix-synapse/redlight.log')
file_handler.setLevel(logging.INFO)
# 2. Define the format for the logs.
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

# 3. Initialize the logger for this module and set its level.
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
# 4. Attach the file handler to the logger.
logger.addHandler(file_handler)

# Prevent this logger's messages from being passed to the root logger or other handlers.
logger.propagate = False

class RedlightServerModule:
    def __init__(self, config: dict, api: ModuleApi):
        self._api = api

        # Register a new web endpoint "/_matrix/loj/v1/abuse_lookup" which will be handled by RedlightServerResource.
        api.register_web_resource(
            "/_matrix/loj/v1/abuse_lookup",
            RedlightServerResource(self)
        )

        logger.info("RedlightServerModule initialized.")

class RedlightServerResource:
    # This flag helps Twisted identify this as a final resource and not look for children.
    isLeaf = True

    def __init__(self, module):
        self._module = module

    # Handle incoming HTTP requests to the registered endpoint.
    def render(self, request):
        # Extract HTTP method (GET, PUT, POST, etc.) from the request.
        method = request.method.decode('ascii')
        # Based on the method, try to find the respective handler function.
        handler = getattr(self, f"on_{method}", None)

        # If a handler is found, process the request with it.
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
            return NOT_DONE_YET  # indicates asynchronous processing
        else:
            # If no handler is found for the method, return "Method Not Allowed".
            return self.method_not_allowed(request)

    # Handle PUT requests to the endpoint.
    @inlineCallbacks
    def on_PUT(self, request):
        try:
            # Read and decode the request body.
            body = yield request.content.read()
            content = body.decode("utf-8")
            logger.info(f"Received abuse lookup request: {content}")

            # Extract specific data points from the request content.
            data = json.loads(content)
            room_id_hash = data["room_id_hash"]
            user_id_hash = data["user_id_hash"]

            # Placeholder check for abuse based on the room_id_hash. 
            # In a real-world scenario, you'd likely check against a database or a list.
            is_abuse = room_id_hash == "ee180279a57f716e5801335a2914e228667f363e460ccabcc49e8fd879e1be4a"

            # Respond based on whether the request is identified as abusive or not.
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

    # Handle GET requests (by disallowing them).
    def on_GET(self, request):
        return self.method_not_allowed(request)

    # Handle POST requests (by disallowing them).
    def on_POST(self, request):
        return self.method_not_allowed(request)

    # General method to respond with "Method Not Allowed" for disallowed or unrecognized HTTP methods.
    def method_not_allowed(self, request):
        request.setResponseCode(405)
        return json.dumps({"error": "Method Not Allowed"}).encode("utf-8")

# Function to parse the configuration for this module.
def parse_config(config: dict) -> dict:
    return config

# Factory function to create and return an instance of the RedlightServerModule.
def create_module(api: ModuleApi, config: dict) -> RedlightServerModule:
    return RedlightServerModule(config, api)
