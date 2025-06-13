from typing import Literal

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from langchain_cohere import ChatCohere
import os
from dotenv import load_dotenv
load_dotenv()
#---- Set OpenAI API key 
# Change environment variable name from "OPENAI_API_KEY" to the name given in 
# your .env file.
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
COHERE_API_KEY = os.getenv['COHERE_API_KEY']


class web_search(BaseModel):
    """
    Use this for general knowledge, real-world events, or questions unrelated to Building Services, such as sports, politics, pop culture, or current news.
    """

class vectorstore(BaseModel):
    """
    Use this only for technical questions about Building Services, such as construction works, and any legislations.
    """

preamble = """
You are an intelligent router for user questions. 
Route each question to one of two tools: 'vectorstore' or 'web_search'.

Use 'vectorstore' when:
- The question is technical, instructional, or factual about built environments.
- It relates to construction, engineering, HVAC, energy use, fire safety, plumbing, or legislation.
- It is likely to be answered using previously stored internal documentation.

Use 'web_search' when:
- The topic is about current events, sports, people, or news.
- It is opinion-based, open-ended, casual, or unrelated to building systems.

Think carefully. Choose the most appropriate tool for this question.
"""


llm = ChatCohere(model="command-r", temperature=0)
structured_llm_router = llm.bind_tools(tools=[web_search, vectorstore], preamble=preamble)

route_prompt = ChatPromptTemplate.from_messages(
    [
        ("human","{question}"),
    ]
)
question_router = route_prompt | structured_llm_router
response = question_router.invoke({"question": "Who will the Bears draft first in the NFL draft?"})
print(response.response_metadata['tool_calls'])
response = question_router.invoke({"question": "What are the types of agent memory?"})
print(response.response_metadata['tool_calls'])
response = question_router.invoke({"question": "Hi how are you?"})
print('tool_calls' in response.response_metadata)