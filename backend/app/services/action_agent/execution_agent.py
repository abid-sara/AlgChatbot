from langchain.prompts import PromptTemplate

class ExecutionAgent:
    """Executes the chosen API and handles missing parameters."""

    def __init__(self, tools, llm):
        self.tools = {t.name: t for t in tools}
        self.llm = llm
        
        self.missing_params_prompt = PromptTemplate(
            template="""
Ask the user for the missing parameters in a natural, conversational way.

API: {api_name}
Missing parameters: {missing_params}

Instructions:
- Ask for the missing parameters in a friendly way
- Use the same language as the user's original query example if query is in french respond in french
- Don't list parameters mechanically, phrase it naturally
- For multiple parameters, ask in a single cohesive sentence
- Ask the user directly (without prefacing or explaining) for the missing parameters but in a very friendly tone
- Respond ONLY with the message you would say to the user, no explanations, no introductions

Respond naturally:
""",
            input_variables=["api_name", "missing_params"]
        )

    def execute(self, api_name: str, params: dict) -> dict:
        tool = self.tools.get(api_name)
        if not tool:
            return {"status": "error", "result": "Unknown API error."}

        # Get required parameters from the tool's schema dynamically
        required_params = list(tool.args_schema.schema()["properties"].keys())
        
        # Check for missing parameters
        missing = []
        for param in required_params:
            if param not in params or params[param] in (None, "", "null"):
                missing.append(param)
        
        if missing:
            # Generate natural language request for missing parameters
            message = self._generate_missing_params_message(api_name, missing)
            
            return {
                "status": "missing_params",
                "missing": missing,
                "message": message
            }

        # Filter params to only include expected ones
        filtered_params = {k: v for k, v in params.items() if k in required_params}
        
        try:
            result = tool.run(filtered_params)
            return {
                "status": "success",
                "result": result
            }
        except Exception as e:
            return {
                "status": "error",
                "result": f"Execution error: {str(e)}"
            }

    def _generate_missing_params_message(self, api_name: str, missing_params: list) -> str:
        """Generate natural language request for missing parameters"""
        
        # Get parameter descriptions from the tool schema
        tool = self.tools.get(api_name)
        param_descriptions = {}
        if tool:
            schema_properties = tool.args_schema.schema()["properties"]
            param_descriptions = {
                param_name: prop.get("description", param_name) 
                for param_name, prop in schema_properties.items()
            }
        
        chain = self.missing_params_prompt | self.llm
        response = chain.invoke({
            "api_name": api_name,
            "missing_params": [param_descriptions.get(param, param) for param in missing_params]
        })
        
        return response.strip()