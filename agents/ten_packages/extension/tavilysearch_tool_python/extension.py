#
#
# Agora Real Time Engagement
# Created by Wei Hu in 2024-08.
# Copyright (c) 2024 Agora IO. All rights reserved.
#
#
import json
import aiohttp
from typing import Any, List

from ten import (
    Cmd,
)
from ten.async_ten_env import AsyncTenEnv
from ten_ai_base.config import BaseConfig
from ten_ai_base.types import LLMToolMetadata, LLMToolMetadataParameter, LLMToolResult
from ten_ai_base.llm_tool import AsyncLLMToolBaseExtension

CMD_TOOL_REGISTER = "tool_register"
CMD_TOOL_CALL = "tool_call"
CMD_PROPERTY_NAME = "name"
CMD_PROPERTY_ARGS = "args"

TOOL_REGISTER_PROPERTY_NAME = "name"
TOOL_REGISTER_PROPERTY_DESCRIPTON = "description"
TOOL_REGISTER_PROPERTY_PARAMETERS = "parameters"
TOOL_CALLBACK = "callback"

TOOL_NAME = "tavily_search"
TOOL_DESCRIPTION = "Use Tavily API to search for latest information. Call this function if you are not sure about the answer."
TOOL_PARAMETERS = {
    "type": "object",
    "properties": {
        "query": {
            "type": "string",
            "description": "The search query to call Tavily Search.",
        }
    },
    "required": ["query"],
}

PROPERTY_API_KEY = "api_key"  # Required

class TavilySearchToolConfig(BaseConfig):
    api_key: str = ""

class TavilySearchToolExtension(AsyncLLMToolBaseExtension):

    def __init__(self, name: str) -> None:
        super().__init__(name)
        self.session = None
        self.config = None
        self.k = 10

    async def on_init(self, ten_env: AsyncTenEnv) -> None:
        ten_env.log_debug("on_init")
        self.session = aiohttp.ClientSession()
        await super().on_init(ten_env)

    async def on_start(self, ten_env: AsyncTenEnv) -> None:
        ten_env.log_debug("on_start")
        await super().on_start(ten_env)

        self.config = await TavilySearchToolConfig.create_async(ten_env=ten_env)

        if not self.config.api_key:
            ten_env.log_info("API key is missing, exiting on_start")
            return

    async def on_stop(self, ten_env: AsyncTenEnv) -> None:
        ten_env.log_debug("on_stop")
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None

    async def on_cmd(self, ten_env: AsyncTenEnv, cmd: Cmd) -> None:
        cmd_name = cmd.get_name()
        ten_env.log_debug(f"on_cmd name {cmd_name}")
        await super().on_cmd(ten_env, cmd)

    def get_tool_metadata(self, ten_env: AsyncTenEnv) -> list[LLMToolMetadata]:
        return [
            LLMToolMetadata(
                name=TOOL_NAME,
                description=TOOL_DESCRIPTION,
                parameters=[
                    LLMToolMetadataParameter(
                        name="query",
                        type="string",
                        description="The search query to call Tavily Search.",
                        required=True,
                    ),
                ],
            )
        ]

    async def run_tool(
        self, ten_env: AsyncTenEnv, name: str, args: dict
    ) -> LLMToolResult | None:
        if name == TOOL_NAME:
            result = await self._do_search(ten_env, args)
            return {"content": json.dumps(result)}

    async def _do_search(self, ten_env: AsyncTenEnv, args: dict) -> Any:
        if "query" not in args:
            raise ValueError("Failed to get property 'query'")
        query = args["query"]
        snippets = []
        results = await self._tavily_search_results(ten_env, query)
        if len(results) == 0:
            return "No good Tavily Search Result was found"
        for result in results:
            snippets.append(result["content"])  # Tavily uses 'content' instead of 'snippet'
        return snippets

    async def _initialize_session(self, ten_env: AsyncTenEnv):
        if self.session is None or self.session.closed:
            ten_env.log_debug("Initializing new session")
            self.session = aiohttp.ClientSession()

    async def _tavily_search_results(self, ten_env: AsyncTenEnv, search_term: str) -> List[dict]:
        await self._initialize_session(ten_env)
        
        # Create Tavily client instance
        from tavily import TavilyClient
        client = TavilyClient(api_key=self.config.api_key)
        
        try:
            # Make the search request
            response = await client.search(
                query=search_term,
                max_results=self.k,
                search_depth="basic"
            )
            
            # Return the results
            if "results" in response:
                return response["results"]
            return []
            
        except Exception as e:
            ten_env.log_error(f"Tavily search error: {str(e)}")
            return []
