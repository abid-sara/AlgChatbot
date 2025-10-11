from langchain.prompts import PromptTemplate
from langchain_core.runnables import RunnableSequence


class ActionIdentifierAgent:
    "Agent that identifies which API/TOOL to use based on the query (user intent from the query)"

    def __init__(self, llm, tools):
        self.llm = llm
        self.tools = tools

        tool_description = "\n".join(
            [f"- {t.name}: {t.description}" for t in tools]
        )

        self.prompt = PromptTemplate(
            template=f"""
You are an API action identifier.
Based on the user request, choose the correct API to use.
Available APIs:
{tool_description}
Return ONLY the API name (e.g. 'signaler_derangement').
User query: {{query}}
""",
input_variables=["query"],
        )

        self.chain = self.prompt | self.llm
    
    def identify(self, query: str) -> str:
        result = self.chain.invoke({"query": query})
        return result.strip().split()[0]