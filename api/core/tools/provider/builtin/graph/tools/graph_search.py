import msal
import requests
from typing import Dict, Any
from core.tools.tool.builtin_tool import BuiltinTool
from core.tools.entities.tool_entities import ToolInvokeMessage
import logging

# Configure logging
logging.basicConfig(filename='graph_search_tool.log', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class GraphSearchTool(BuiltinTool):
    def set_runtime(self, credentials: Dict[str, Any]):
        self.runtime = type('Runtime', (object,), {})()
        self.runtime.credentials = credentials
        self.runtime.tenant_id = credentials.get('tenant_id')
        self.runtime.runtime_parameters = {}
        logging.debug(f"Runtime credentials set: {self.runtime.credentials}")

    def _invoke(self, user_id: str, tool_parameters: Dict[str, Any]) -> ToolInvokeMessage:
        logging.debug("Invoking tool with parameters: %s", tool_parameters)
        query = tool_parameters['query']
        client_id = self.runtime.credentials['client_id']
        client_secret = self.runtime.credentials['client_secret']
        tenant_id = self.runtime.credentials['tenant_id']
        region = self.runtime.credentials.get('region', 'US')

        
        token = self.get_access_token(client_id, client_secret, tenant_id)
        results = self.search_content(query, token, region)
        
        extracted_data = self.extract_relevant_data(results)
        
        return self.create_text_message(text=self.format_results(extracted_data))

    def get_access_token(self, client_id, client_secret, tenant_id):
        logging.debug("Getting access token")
        authority = f"https://login.microsoftonline.com/{tenant_id}"
        app = msal.ConfidentialClientApplication(client_id, authority=authority, client_credential=client_secret)
        result = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
        if "access_token" in result:
            logging.debug("Access token obtained")
            return result["access_token"]
        else:
            logging.error("Failed to obtain access token: %s", result.get("error_description", result))
            raise Exception("Could not obtain access token")

    def search_content(self, query, token, region):
        logging.debug("Searching content with query: %s", query)
        headers = {"Authorization": f"Bearer {token}"}
        search_url = "https://graph.microsoft.com/v1.0/search/query"
        payload = {
            "requests": [
                {
                    "entityTypes": ["driveItem", "listItem", "site"],  # Adjust entity types as needed
                    "query": {"queryString": query},
                    "region": region  
                }
            ]
        }
        
        logging.debug("Request Headers: %s", headers)
        logging.debug("Request Payload: %s", payload)

        response = requests.post(search_url, headers=headers, json=payload)
        try:
            response.raise_for_status()
            logging.debug("Search results obtained")
            return response.json()
        except requests.exceptions.HTTPError as e:
            logging.error("HTTP Error: %d - %s", e.response.status_code, e.response.text)
            raise

    def extract_relevant_data(self, results):
        logging.debug("Extracting relevant data from results")
        relevant_data = []
        for result in results.get('value', []):
            for item in result.get('hitsContainers', []):
                for hit in item.get('hits', []):
                    # Extract relevant information
                    title = hit.get('resource', {}).get('name', 'No Title')
                    link = hit.get('resource', {}).get('webUrl', 'No URL')
                    snippet = hit.get('resource', {}).get('snippet', 'No Snippet')
                    relevant_data.append({
                        'type': 'document',
                        'title': title,
                        'link': link,
                        'snippet': snippet
                    })
        
        logging.debug("Extracted Data: %s", relevant_data)
        return relevant_data

    @staticmethod
    def _process_response(res: dict, typ: str) -> str:
        if typ == 'document':
            return f"Title: {res.get('title', 'No Title')}\nLink: {res.get('link', 'No URL')}\nSnippet: {res.get('snippet', 'No Snippet')}\n\n"
        return ""

    def format_results(self, data):
        formatted_results = ""
        for item in data:
            formatted_results += self._process_response(item, item['type'])
        return formatted_results
