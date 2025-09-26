from app.services.llm.factory import create_llm
from app.utils.translation import arabic_latin_words

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
2. **For Arabic responses specifically:**
   - Use proper right-to-left (RTL) text formatting
   - Ensure consistent Arabic typography throughout
   - Maintain proper Arabic punctuation (، instead of , and ؟ instead of ?)
   - Keep Arabic text properly aligned and structured
3. Provide clear, concise, and easy-to-understand answers.
4. Use a courteous and professional customer service tone.
5. If the user asks about a specific service (e.g., E-facture, Idoom ADSL, Fibre), only quote points present in the documents.
6. If no direct answer is available, say: "This information is not available in the documentation."
7. If the question is a continuation, ensure consistency with previous messages.
8. Always return the final answer as **well-formatted Markdown** with:
   - Headings using ### (for Arabic: ### العنوان)
   - Bullet lists using - or * (maintain consistent spacing)
   - **Bold** for important terms (Arabic: **النص المهم**)
   - Tables when listing structured data (plans, prices, comparisons)
   - Proper line breaks and spacing for readability
9. **Formatting requirements:**
   - Do NOT use inline stars `*` for bullets. Use proper Markdown syntax.
   - Links must be valid Markdown links: [text](url)
   - For Arabic text, ensure proper spacing between Arabic and Latin text
   - Maintain consistent indentation for nested lists
10. Do NOT start your response with meta-phrases like "Yes, I will answer your question based on the documentation."
11. Do not mention document numbers or file names in the answer (example: write "MY IDOOM: A mobile application from Algérie Télécom" instead of "MY IDOOM: A mobile application from Algérie Télécom ([Document 14])")
12. Provide the answer directly, without unnecessary introductions or meta-comments.
13. Avoid repetition (don't write "Idoom ADSL\\nIdoom ADSL")
14. **Arabic-Latin service mapping:** If the user mentions an Arabic service/offer name, map it to its Latin equivalent using this dictionary:

{arabic_latin_words}

Note: Only translate service/offer names, not regular Arabic words used in normal sentences.

15. **Text direction and structure:**
    - For mixed Arabic-Latin content, ensure proper bidirectional text handling
    - Keep service names and technical terms in their original Latin form even within Arabic responses
    - Maintain consistent paragraph structure and spacing

Answer:
"""
        return prompt
