from langchain.tools import Tool

from server.agent.tools import *
from server.agent.tools.aime_qa import qa_tool, FQAInput
from server.agent.tools.cashback_retriever import get_aime_retriever, aimeInput

## 请注意，如果你是为了使用AgentLM，在这里，你应该使用英文版本。

tools = [
    Tool.from_function(
        func=calculate,
        name="calculate",
        description="Useful for when you need to answer questions about simple calculations",
        args_schema=CalculatorInput,
    ),
    Tool.from_function(
        func=arxiv,
        name="arxiv",
        description="A wrapper around Arxiv.org for searching and retrieving scientific articles in various fields.",
        args_schema=ArxivInput,
    ),
    Tool.from_function(
        func=weathercheck,
        name="weather_check",
        description="",
        args_schema=WhetherSchema,
    ),
    Tool.from_function(
        func=shell,
        name="shell",
        description="Use Shell to execute Linux commands",
        args_schema=ShellInput,
    ),
    Tool.from_function(
        func=search_knowledgebase_complex,
        name="search_knowledgebase_complex",
        description="Use Use this tool to search local knowledgebase and get information",
        args_schema=KnowledgeSearchInput,
    ),
    Tool.from_function(
        func=search_internet,
        name="search_internet",
        description="Use this tool to use bing search engine to search the internet",
        args_schema=SearchInternetInput,
    ),
    Tool.from_function(
        func=wolfram,
        name="Wolfram",
        description="Useful for when you need to calculate difficult formulas",
        args_schema=WolframInput,
    ),
    Tool.from_function(
        func=search_youtube,
        name="search_youtube",
        description="use this tools to search youtube videos",
        args_schema=YoutubeInput,
    ),
]

aime_tools = [
    Tool(
        name="ensemble_search",
        func=get_aime_retriever,
        description="useful for when you need to query the cashback or coupon data of related brands",
        return_direct=True,
        args_schema=aimeInput,
    ),
    Tool.from_function(
        func=qa_tool,
        name="fqa_search",
        description="useful for when you ask questions about FQA about cashback.ai or cashback or coupon.",
        return_direct=True,
        args_schema=FQAInput,
    ),
]

aime_tools_names = [tool.name for tool in aime_tools]

tool_names = [tool.name for tool in tools]
