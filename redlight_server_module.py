import logging
import json
import requests
import base64
import datetime
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

class SourceDataManager:
    def __init__(self, module, config):
        self._module = module
        self._source_repo_url = config.get("redlight_source_repo_url", "")
        self._git_token = config.get("redlight_git_token", "")
        self._source_list_file_path = config.get("redlight_source_list_file_path", "dist/summaries.json")
        self._filtered_tags = config.get("filtered_tags", [])
        self._source_dict = {}
        self._source_dict_last_update = None
        self.update_data()

    def fetch_file_from_gitea(self, repo_url, token, file_path):
        # Construct the API URL for the file.
        base_url = repo_url.rstrip("/")
        api_url = f"{base_url}/contents/{file_path}?ref=main&access_token={token}"

        # Log attempt to fetch the file.
        logger.info(f"Attempting to update source list, fetching file from: {api_url}")

        response = requests.get(api_url)

        if response.status_code == 200:
            content_base64 = response.json().get("content")
            if content_base64:
                decoded_content = base64.b64decode(content_base64).decode('utf-8')
                # Log success
                logger.info(f"Successfully fetched content with length: {len(decoded_content)} characters.")
                return decoded_content
            else:
                error_message = "Content not found in the response!"
                logger.error(error_message)
                raise ValueError(error_message)
        else:
            error_message = f"Failed to fetch file. Response code: {response.status_code}. Content: {response.content.decode('utf-8')}"
            logger.error(error_message)
            response.raise_for_status()

    def update_data(self):
        now = datetime.datetime.now()
        if not self._source_dict_last_update or (now - self._source_dict_last_update).total_seconds() > 3600:
            raw_content = self.fetch_file_from_gitea(self._source_repo_url, self._git_token, self._source_list_file_path)
            content = json.loads(raw_content)

            self._source_dict = {
                report["room"]["room_id_hash"]: report["report_id"]
                for report in content
                if any(tag in self._filtered_tags for tag in report["report_info"]["tags"])
            }

            self._source_dict_last_update = now
            logger.info(f"Source data updated. Number of reports matching the filtered tags: {len(self._source_dict)}")

    def get_data(self):
        self.update_data()
        return self._source_dict

class RedlightServerModule:
    def __init__(self, config: dict, api: ModuleApi):
        self._api = api

        # Register a new web endpoint "/_matrix/loj/v1/abuse_lookup" which will be handled by RedlightServerResource.
        api.register_web_resource(
            "/_matrix/loj/v1/abuse_lookup",
            RedlightServerResource(config, self)
        )

        logger.info("RedlightServerModule initialized.")

class RedlightServerResource:
    # This flag helps Twisted identify this as a final resource and not look for children.
    isLeaf = True

    def __init__(self, config: dict, module):
        self._module = module
        self._data_manager = SourceDataManager(module, config)
        self._source_dict = self._data_manager.get_data()
        self._client_api_tokens = config.get("redlight_client_tokens", [])
        self._filtered_tags = config.get("redlight_filtered_tags", [])
        # Logging for debug purposes
        logger.debug(f"Filtered room_id_hashes: {list(self._source_dict.keys())}")

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
            # Indicates asynchronous processing.
            return NOT_DONE_YET
        else:
            logger.warning(f"Received a request with unsupported method: {method}")
            # If no handler is found for the method, return "Method Not Allowed".
            return self.method_not_allowed(request)

    # Handle PUT requests to the endpoint.
    @inlineCallbacks
    def on_PUT(self, request):
        logger.info(f"Processing PUT request from {request.getClientIP()}.")
        try:
            # Read and decode the request body.
            body = yield request.content.read()
            content = body.decode("utf-8")
            logger.info(f"Received abuse lookup request: {content}")

            # Extract specific data points from the request content.
            data = json.loads(content)
            room_id_hash = data["room_id_hash"]
            user_id_hash = data["user_id_hash"]
            api_token = data["api_token"]

            # Check if the provided API token is valid.
            if api_token not in self._client_api_tokens:
                logger.warning(f"Invalid API token provided by {request.getClientIP()}.")
                request.setResponseCode(401)
                defer.returnValue(json.dumps({"error": "Unauthorized"}).encode("utf-8"))
                return

            # Update and fetch the source_dict when required.
            source_dict = self._data_manager.get_data()

            # Check for abuse based on the room_id_hash and the filtered source list.
            is_abuse = room_id_hash in source_dict

            # Respond based on whether the request is identified as abusive or not.
            if is_abuse:
                report_id = source_dict[room_id_hash]
                logger.warning(f"Abuse detected from {request.getClientIP()}, user_id_hash: {user_id_hash} report_id: {report_id}.")
                logger.debug(f"room_id_hash: {room_id_hash}.")
                request.setResponseCode(http.OK)
                defer.returnValue(json.dumps({
                    "error": None,
                    "report_id": report_id,
                }).encode("utf-8"))
            else:
                logger.info(f"No abuse detected for request from {request.getClientIP()}.")
                request.setResponseCode(http.NO_CONTENT)
                defer.returnValue(b"")

        except Exception as e:
            logger.error(f"Error processing abuse lookup PUT request from {request.getClientIP()}: {e}")
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
        logger.warning(f"Method Not Allowed: {request.method.decode('ascii')} from {request.getClientIP()}.")
        request.setResponseCode(405)
        return json.dumps({"error": "Method Not Allowed"}).encode("utf-8")

# Function to parse the configuration for this module.
def parse_config(config: dict) -> dict:
    return config

# Factory function to create and return an instance of the RedlightServerModule.
def create_module(api: ModuleApi, config: dict) -> RedlightServerModule:
    return RedlightServerModule(config, api)
