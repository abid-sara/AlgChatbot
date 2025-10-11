from langchain.prompts import PromptTemplate
from app.services.action_agent.action_identifier_agent import ActionIdentifierAgent
from app.services.action_agent.execution_agent import ExecutionAgent
from app.services.action_agent.parameter_extractor_agent import ParameterExtractorAgent
from app.services.action_agent.tools.api_functions import api_tools
from app.services.llm.factory import create_llm
from app.utils.conversation_manager import ConversationManager

class ActionAgentController:
    def __init__(self):
        self.llm = create_llm()
        
        self.identifier = ActionIdentifierAgent(self.llm, api_tools)
        self.extractor = ParameterExtractorAgent(self.llm, api_tools)  # Changed: added tools parameter
        self.executor = ExecutionAgent(api_tools, self.llm)
        self.conversation_manager = ConversationManager() 

        self.pending_actions = {}
        
        # New: Continuation detection prompt
        self.continuation_prompt = PromptTemplate(
            template="""
Determine if the user's query is providing missing parameters for a pending action or starting a new request.

Context:
- Pending API: {pending_api}
- Missing parameters: {missing_params}
- User's previous query: {previous_query}

Current user query: "{current_query}"

Instructions:
- If the user is providing values for the missing parameters (either explicitly or implicitly), respond with "continuation"
- If the user is asking a completely new question or starting a different action, respond with "new"
- If it's unclear, consider the context and intent

Respond with ONLY one word: either "continuation" or "new"
""",
            input_variables=["pending_api", "missing_params", "previous_query", "current_query"]
        )

    def handle_action(self, query, user_id="default"):
        self.conversation_manager.add_message(user_id, "user", query)
        
        # Check if we have a pending action for this user
        if user_id in self.pending_actions:
            is_continuation = self._detect_continuation(query, user_id)
            
            if is_continuation:
                print(f"Detected continuation for user {user_id}")
                return self._handle_pending_action(query, user_id)
            else:
                print(f"Detected new action - discarding pending action for user {user_id}")
                del self.pending_actions[user_id]
                return self._handle_new_action(query, user_id)
        else:
            return self._handle_new_action(query, user_id)

    def _detect_continuation(self, query: str, user_id: str) -> bool:
        """Use LLM to determine if the query is continuing a pending action"""
        pending = self.pending_actions[user_id]
        
        # Get conversation history for context
        conversation_history = self.conversation_manager.get_conversation(user_id)
        previous_query = ""
        
        if conversation_history and len(conversation_history) > 1:
            # Get the last user message before the current one
            previous_messages = [msg for msg in conversation_history if msg["role"] == "user"]
            if len(previous_messages) > 1:
                previous_query = previous_messages[-2]["content"]
        
        chain = self.continuation_prompt | self.llm
        response = chain.invoke({
            "pending_api": pending["api_name"],
            "missing_params": ", ".join(pending["missing"]),
            "previous_query": previous_query,
            "current_query": query
        })
        
        result = response.strip().lower()
        print(f"Continuation detection result: {result}")
        
        return result == "continuation"

    def _handle_pending_action(self, query: str, user_id: str) -> str:
        """Handle continuation of pending action with missing parameters"""
        pending = self.pending_actions[user_id]
        api_name = pending["api_name"]
        params = pending["params"]

        # Extract parameters from the new query
        new_params = self.extractor.extract(api_name, query)
        print(f"Extracted continuation params for {api_name}: {new_params}")

        # Update missing parameters with new values
        updated_count = 0
        for param_name in pending["missing"][:]:  # Copy the list to iterate safely
            if new_params.get(param_name) not in (None, "", "null"):
                params[param_name] = new_params[param_name]
                pending["missing"].remove(param_name)
                updated_count += 1
                print(f"Updated parameter {param_name}: {new_params[param_name]}")
        
        # If no parameters were updated, try to extract parameters differently
        if updated_count == 0:
            params = self._extract_parameters_from_text(api_name, query, pending["missing"], params)
        
        # Retry execution
        response = self.executor.execute(api_name, params)

        if response["status"] == "missing_params":
            # Still missing parameters, update pending action
            pending["params"] = params
            pending["missing"] = response["missing"]
            self.pending_actions[user_id] = pending

            self.conversation_manager.add_message(user_id, "assistant", response["message"])
            return response["message"]
        
        # Success - clear pending action
        del self.pending_actions[user_id]
        self.conversation_manager.add_message(user_id, "assistant", response["result"])
        return response["result"]

    def _extract_parameters_from_text(self, api_name: str, query: str, missing_params: list, current_params: dict) -> dict:
        """Extract specific missing parameters from text when standard extraction fails"""
        params = current_params.copy()
        
        for param_name in missing_params:
            # Use a simple prompt to extract just this parameter
            prompt = PromptTemplate(
                template="""
Extract the value for parameter "{param_name}" from the user's query.

User query: "{query}"

If the parameter value is present in the query, return ONLY the value.
If the parameter value is not present, return "null".

Parameter to extract: {param_name}
Value: 
""",
                input_variables=["param_name", "query"]
            )
            
            chain = prompt | self.llm
            result = chain.invoke({"param_name": param_name, "query": query})
            value = result.strip()
            
            if value and value.lower() != "null":
                params[param_name] = value
                print(f"Direct extraction - {param_name}: {value}")
        
        return params

    def _handle_new_action(self, query: str, user_id: str) -> str:
        """Handle new action request"""
        # Identify API
        api_name = self.identifier.identify(query)
        print(f"Identified API: {api_name}")
        
        if not api_name or api_name not in [tool.name for tool in api_tools]:
            error_msg = "Je n'ai pas pu identifier l'action que vous souhaitez effectuer. Pouvez-vous reformuler votre demande ?"
            self.conversation_manager.add_message(user_id, "assistant", error_msg)
            return error_msg
        
        # Extract parameters
        params = self.extractor.extract(api_name, query)
        print(f"Extracted parameters: {params}")
        
        # Execute
        response = self.executor.execute(api_name, params)
        print(f"Execution response: {response}")

        # Handle missing parameters
        if response["status"] == "missing_params":
            self.pending_actions[user_id] = {
                "api_name": api_name,
                "params": params,
                "missing": response["missing"],
                "original_query": query
            }
            self.conversation_manager.add_message(user_id, "assistant", response["message"])
            return response["message"]

        # Success or error
        self.conversation_manager.add_message(user_id, "assistant", response["result"])
        return response["result"]