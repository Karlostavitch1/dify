import logging
from typing import Dict, Any
from core.tools.provider.builtin_tool_provider import BuiltinToolProviderController
from core.tools.errors import ToolProviderCredentialValidationError
from core.tools.provider.builtin.graph.tools.graph_search import GraphSearchTool

class GraphProvider(BuiltinToolProviderController):
    def _validate_credentials(self, credentials: Dict[str, Any]) -> None:
        try:
            logging.debug("Validating credentials")
            tool = GraphSearchTool()
            tool.set_runtime(credentials)
            tool.invoke(user_id='', tool_parameters={"query": "test"})
            logging.debug("Credentials validated successfully")
        except Exception as e:
            logging.error("Error validating credentials: %s", e)
            raise ToolProviderCredentialValidationError(str(e))
