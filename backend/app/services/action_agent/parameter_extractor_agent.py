from langchain.prompts import PromptTemplate
import json
import re

class ParameterExtractorAgent:
    """Extracts parameters from user query for the selected API."""

    def __init__(self, llm, tools):
        self.llm = llm
        self.tools = {t.name: t for t in tools}

    def extract(self, api_name: str, query: str) -> dict:
        tool = self.tools.get(api_name)
        if not tool:
            return {}
        
        # Get parameter schema dynamically from the tool
        schema_properties = tool.args_schema.schema()["properties"]
        param_descriptions = []
        
        for param_name, param_info in schema_properties.items():
            desc = param_info.get("description", "")
            param_type = param_info.get("type", "string")
            param_descriptions.append(f"- {param_name} ({param_type}): {desc}")
        
        param_list = "\n".join(param_descriptions)
        
        prompt = PromptTemplate(
            template="""
Extract parameters from the user query for the API call. 

API: {api_name}
Parameters needed:
{param_list}

Instructions:
- Extract parameter values from the query
- For missing parameters, use null
- Return pure JSON without any additional text

User query: {query}
JSON output:
""",
            input_variables=["api_name", "query", "param_list"],
        )

        chain = prompt | self.llm
        result = chain.invoke({
            "api_name": api_name, 
            "query": query, 
            "param_list": param_list
        })
        
        print(f"Raw extraction result for {api_name}: {result}")
        
        try:
            cleaned_result = result.strip()
            json_match = re.search(r'\{[^{}]*\{.*\}[^{}]*\}|\{.*\}', cleaned_result, re.DOTALL)
            if json_match:
                cleaned_result = json_match.group()
            
            extracted_params = json.loads(cleaned_result)
            print(f"Successfully extracted parameters: {extracted_params}")
            return extracted_params
            
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}. Raw result: {result}")
            return self._create_empty_params(api_name)
        except Exception as e:
            print(f"Unexpected error in parameter extraction: {e}")
            return self._create_empty_params(api_name)
    
    def _create_empty_params(self, api_name: str) -> dict:
        """Create empty parameters structure based on API schema"""
        tool = self.tools.get(api_name)
        if not tool:
            return {}
        
        schema_properties = tool.args_schema.schema()["properties"]
        empty_params = {param: None for param in schema_properties.keys()}
        return empty_params