from backend.app.services.llm.factory import create_llm


class ContinuationService:
    def __init__(self):
        self.model = create_llm()

    def is_continuation(self, conversation_manager, user_query):
        """
        Determines if the user_query is a continuation of the conversation.
        Returns:
            dict with keys:
                - is_continuation (bool)
                - continuation_type (e.g., 'question', 'action', or None)
        """
        
        previous_context = conversation_manager.get_context()
        messages = previous_context + [
            {"role": "user", "content": user_query}
        ]

        prompt = (
            "Given the following conversation history, and the user's latest query, "
            "determine if the latest query is a continuation of a previous question, "
            "a continuation of an action (e.g., providing parameters), or a new topic. "
            "Reply with 'question_continuation', 'action_continuation', or 'new'.\n\n"
            f"Conversation:\n{messages}"
        )

        llm_response = self.llm.ask(prompt)
        if "question_continuation" in llm_response.lower():
            return {"is_continuation": True, "continuation_type": "question"}
        elif "action_continuation" in llm_response.lower():
            return {"is_continuation": True, "continuation_type": "action"}
        else:
            return {"is_continuation": False, "continuation_type": None}