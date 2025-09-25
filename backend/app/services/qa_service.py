from app.services.llm.factory import create_llm

class QAService:
    def __init__(self):
        """Initialize the QA service with the configured LLM"""
        self.model = create_llm()

    def preprocess_query(self, query, conversation_history=None):
        """
        Pre-process the query: only check if it's a continuation based on history.
        """
        if not conversation_history or len(conversation_history) == 0:
            return {
                "processed_query": query,
                "is_continuation": False
            }

        analysis_prompt = self._build_analysis_prompt(query, conversation_history)

        try:
            response = self.model.generate_content(analysis_prompt)
            response_text = response.text.strip().lower()

            # Default values
            is_continuation = False
            processed_query = query

            # Parse continuation
            if "is_continuation:" in response_text:
                val = response_text.split("is_continuation:")[1].split("\n")[0].strip()
                is_continuation = val == "true"

            # Parse processed query
            if "processed_query:" in response_text:
                val = response_text.split("processed_query:")[1].split("\n")[0].strip()
                if val:
                    processed_query = val

            return {
                "processed_query": processed_query,
                "is_continuation": is_continuation
            }

        except Exception as e:
            print(f"Error in query pre-processing: {e}")
            return {
                "processed_query": query,
                "is_continuation": False
            }

    def _build_analysis_prompt(self, query, conversation_history):
        """
        Build a prompt for analyzing if the new query is a continuation.
        """
        history_text = ""
        for msg in conversation_history[-3:]:
            role = "User" if msg["role"] == "user" else "Assistant"
            history_text += f"{role}: {msg['content']}\n"

        prompt = f"""
You are a continuation detector for a customer service chatbot.
Your task is to decide if the new user question is a logical continuation
of the recent conversation.

Recent conversation history:
{history_text}

New user question:
{query}

Output ONLY in this format:
is_continuation: [true/false]
processed_query: [the clarified or reformulated question if needed, otherwise repeat the original question]
"""
        return prompt

    def generate_answer(self, query, context_chunks, conversation_history=None):
        query_info = self.preprocess_query(query, conversation_history)
        processed_query = query_info["processed_query"]
        is_continuation = query_info["is_continuation"]

        prompt = self._build_prompt(
            processed_query, context_chunks, conversation_history, is_continuation
        )

        try:
            response = self.model.generate_content(prompt)

            # Gemini returns .text ; OpenAI returns .choices
            if hasattr(response, "text"):
                answer = response.text
            else:
                answer = response.choices[0].message.content

            return {
                "answer": answer.strip(),
                "status": "success",
                "is_continuation": is_continuation,
            }

        except Exception as e:
            return {
                "answer": "Sorry, an error occurred while processing your request.",
                "status": "error",
                "error": str(e),
            }


    def stream_answer_tokens(self, query, context_chunks, conversation_history=None):
        """
        Unified streaming generator for Gemini, Qwen.
        """
        query_info = self.preprocess_query(query, conversation_history)
        processed_query = query_info["processed_query"]
        is_continuation = query_info["is_continuation"]

        prompt = self._build_prompt(
            processed_query, context_chunks, conversation_history, is_continuation
        )

        collected = ""
        try:
            stream = self.model.stream_content(prompt)

            # ---- Gemini streaming ----
            if stream.__class__.__name__ == "Generator":
                for chunk in stream:
                    if hasattr(chunk, "candidates"):
                        c = chunk.candidates[0]
                        if hasattr(c, "content") and c.content.parts:
                            text = c.content.parts[0].text
                            if text:
                                collected += text
                                yield text
            else:
                for chunk in stream:
                    if chunk.candidates and chunk.candidates[0].content.parts:
                        yield chunk.candidates[0].content.parts[0].text

        except Exception as e:
             # Streaming failed (e.g., Gemini 503) switching back to block 
            print(f"[Stream error] {e} — switching to fallback single call")
            try:
               
                response = self.model.generate_content(prompt)
                full_answer = getattr(response, "text", None) or \
                              response.choices[0].message.content
                
                if full_answer:
                    # Remove already-streamed part if the model restarted the answer
                    if full_answer.startswith(collected[:50]):  
                        remainder = full_answer[len(collected):]
                    else:
                        remainder = "\n\n" + full_answer

                    yield "\n\n" + remainder.strip()
                
                else:
                    yield "\n Incomplete response, the service is interrupted."
            except Exception as e2:
                yield f"\nImpossible to get back the end of the response ({e2})."


    def _build_prompt(self, query, context_chunks, conversation_history=None, is_continuation=False):
        """
        Build a strong multilingual prompt for answer generation.
        """
        conversation_context = ""
        if conversation_history:
            conversation_context = "Recent conversation history:\n\n"
            for msg in conversation_history[-3:]:
                role = "User" if msg["role"] == "user" else "Assistant"
                conversation_context += f"{role}: {msg['content']}\n\n"

        continuation_note = ""
        if is_continuation:
            continuation_note = "This question is a continuation. Keep the previous context in mind.\n\n"

        docs_context = ""
        for i, chunk in enumerate(context_chunks, 1):
            docs_context += f"[Document {i}]\n{chunk}\n\n"

        prompt = f"""
You are an intelligent assistant for **Algeria Telecom**.
Your role is to answer customers using ONLY the information provided below.
Do not make any assumptions. If the answer is not found, clearly state that the information is unavailable.

{conversation_context}
{continuation_note}
User question: {query}

Context from official Algeria Telecom documents:
{docs_context}

Instructions for your response:
1. Respond in the same language as the question (Arabic, French, or English) don't use any other language.
2. Provide clear, concise, and easy-to-understand answers.
3. Use a courteous and professional customer service tone.
4. If the user asks about a specific service (e.g., E-facture, Idoom ADSL, Fibre), only quote points present in the documents.
5. If no direct answer is available, say: "This information is not available in the documentation."
6. If the question is a continuation, ensure consistency with previous messages.
7. Always return the final answer as **Markdown**, well formatted with:
  - Headings (###)
  - Bullet lists (- or *)
  - Bold for important terms
  - Tables when listing structured data (plans, prices, comparisons)
8. Do NOT use inline stars `*` for bullets. Use proper Markdown syntax.
9. Links must be valid Markdown links: [text](url).
10. Do NOT start your response with phrases like "Yes, I will answer your question based on the documentation."
11. Do not mention document numbers or file names in the answer example don't write: MY IDOOM: A mobile application from Algérie Télécom available on Google Play, App Store, and Huawei AppGallery, integrating several services ([Document 14]) write only the phrase MY IDOOM: A mobile application from Algérie Télécom available on Google Play, App Store, and Huawei AppGallery, integrating several services.
12. Provide the answer directly, without unnecessary introductions or meta-comments.


Answer:
"""
        return prompt
