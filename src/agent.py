"""
Build the Pipeline 3 ReAct agent (LangChain classic) with project tools.
"""

from __future__ import annotations

from typing import List

from langchain_classic.agents import AgentExecutor, create_react_agent
from langchain_core.language_models import BaseLanguageModel
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import BaseTool

from src.constants import AGENT_MAX_ITERATIONS
from src.skills import build_agent_system_prompt
from src.tools import get_agent_tools

# Classic ReAct single-input template (tools and tool_names are injected by create_react_agent).
_REACT_TEMPLATE = (
    build_agent_system_prompt()
    + "\n\nYou have access to these tools:\n\n{tools}\n\n"
    "Use this format strictly:\n\n"
    "Question: the input task you must solve\n"
    "Thought: plan your next step\n"
    "Action: the action to take, must be one of [{tool_names}]\n"
    "Action Input: valid JSON inputs for that tool (per tool schema)\n"
    "Observation: tool output\n"
    "... repeat Thought/Action/Action Input/Observation as needed ...\n"
    "Thought: I have completed detection and recorded the result.\n"
    "Final Answer: short summary stating CLONE or NOT_CLONE and that write_result was called.\n\n"
    "Begin!\n\n"
    "Question: {input}\n"
    "Thought:{agent_scratchpad}"
)


def build_react_executor(llm: BaseLanguageModel) -> AgentExecutor:
    """
    Create an AgentExecutor with ReAct prompting and repository tools.

    Args:
        llm: Chat model from :mod:`src.llm`.

    Returns:
        Configured AgentExecutor (verbose, bounded iterations, parsing error tolerance).
    """
    tools: List[BaseTool] = get_agent_tools()
    prompt = PromptTemplate.from_template(_REACT_TEMPLATE)
    agent = create_react_agent(llm, tools, prompt)
    return AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        max_iterations=AGENT_MAX_ITERATIONS,
        handle_parsing_errors=True,
    )
