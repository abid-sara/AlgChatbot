import json
import logging
from flask import Blueprint, request, jsonify, Response, stream_with_context
import time

from app.services.search_service import SearchService
from app.services.qa_service import QAService
from app.utils.conversation_manager import ConversationManager
from app.services.action_agent.controller import ActionAgentController
from config.settings import (
    EMBEDDING_MODEL, TFIDF_WEIGHT, BM25_WEIGHT, EMBEDDING_WEIGHT,
    DEFAULT_SEARCH_METHOD, TOP_N_RESULTS, DATA_PATH
)

# Logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Services
search_service = SearchService(
    embedding_model=EMBEDDING_MODEL,
    tfidf_weight=TFIDF_WEIGHT,
    bm25_weight=BM25_WEIGHT,
    embedding_weight=EMBEDDING_WEIGHT,
    search_method=DEFAULT_SEARCH_METHOD
)

qa_service = QAService()
conversation_manager = ConversationManager()
agent = ActionAgentController()

# Blueprint
api = Blueprint('api', __name__)

# ------------------- Health -------------------
@api.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'search_method': search_service.search_method,
        'chunks_count': len(search_service.chunks)
    }), 200

# ------------------- Search -------------------
@api.route('/search', methods=['POST'])
def search():
    data = request.json
    if not data or 'query' not in data:
        return jsonify({'error': 'Query is required'}), 400

    query = data['query']
    top_n = data.get('top_n', TOP_N_RESULTS)
    search_method = data.get('search_method', None)

    results = search_service.search(query, top_n, search_method=search_method)

    response_data = {
    'query': query,
    'results': [
        {'text': chunk, 'score': float(score)}
        for chunk, score in results
    ],
    'count': len(results),
    'method': search_method or search_service.search_method
    }

    return Response(
        json.dumps(response_data, ensure_ascii=False),
        content_type="application/json; charset=utf-8",
        status=200
    )

# ---- QA ---------
import json
from flask import Response

@api.route('/qa', methods=['POST'])
def question_answer():
    """
    Question answering endpoint with conversation context
    
    Expected JSON payload:
    {
        "query": "question"
        "user_id": "unique_user_id",
        "top_n": 5,                    
        "search_method": "hybrid",
        "use_context": true
    }
    """
    data = request.json
    
    if not data or 'query' not in data:
        return Response(
            json.dumps({'error': 'Query is required'}, ensure_ascii=False),
            content_type="application/json; charset=utf-8",
            status=400
        )
    
    query = data['query']
    user_id = data.get('user_id', 'anonymous')
    top_n = data.get('top_n', None)
    search_method = data.get('search_method', None)
    use_context = data.get('use_context', True)
    
    logger.info(f"QA request received for user '{user_id}', query: '{query}', use_context: {use_context}")
    

    conversation_history = conversation_manager.get_conversation(user_id) if use_context else None
    
    # detect continuation 
    query_analysis = qa_service.preprocess_query(query, conversation_history) or {}
    processed_query = query_analysis.get("processed_query", query)
    is_continuation = query_analysis.get("is_continuation", False)
    
    # build retrieval query to have last context query and current query
    retrieval_query = processed_query
    if is_continuation and conversation_history:
        last_user_msgs = [msg["content"] for msg in conversation_history if msg["role"] == "user"]
        if last_user_msgs:
            retrieval_query = f"In the context of: {last_user_msgs[-3:]}, question: {processed_query}"
    
    logger.info(f"Processed query: '{processed_query}', is_continuation: {is_continuation}")
    logger.info(f"Retrieval query: '{retrieval_query}'")
    
    
    t0 = time.time()
    search_results = search_service.search(retrieval_query, top_n, search_method=search_method)
    print("----> Search took", time.time() - t0, "s")
    formatted_chunks = search_service.format_search_results(search_results)
    
    # streaming the answer with original processed query
    def generate():
        try:
            yield f"data: {json.dumps({'event': 'start'})}\n\n"

            for token in qa_service.stream_answer_tokens(processed_query,formatted_chunks, conversation_history):
                yield f"data: {json.dumps({'token': token})}\n\n"
            
            yield f"data: {json.dumps({'event': 'end'})}\n\n"

            #update conversation history
            conversation_manager.add_message(user_id, 'user', query)
            conversation_manager.add_message(user_id, "assistant", "(stream answer)")
        
        except Exception as e:
            yield f"data: {json.dumps({'event': 'error', 'error':str(e)})}\n\n"
        
    return Response(stream_with_context(generate()), mimetype='text/event-stream')


@api.route('/conversation', methods=['POST'])
def update_conversation():
    """
    Update the conversation cache for a user session.
    
    Expected JSON payload:
    {
        "user_id": "unique_user_id",
        "role": "user/assistant",
        "content": "message content"
    }
    """
    data = request.json
    if not data or 'user_id' not in data or 'role' not in data or 'content' not in data:
        return jsonify({'error': 'Invalid payload'}), 400

    user_id = data['user_id']
    role = data['role']
    content = data['content']

    # Add message to conversation manager
    conversation_manager.add_message(user_id, role, content)

    return jsonify({
        'status': 'success', 
        'conversation': conversation_manager.get_conversation(user_id)
    }), 200

@api.route('/conversation/<user_id>', methods=['GET'])
def get_conversation(user_id):
    """
    Retrieve the conversation cache for a user session.
    """
    return jsonify({
        'conversation': conversation_manager.get_conversation(user_id)
    }), 200

@api.route('/conversation/<user_id>', methods=['DELETE'])
def clear_conversation(user_id):
    """
    Clear the conversation history for a user.
    """
    conversation_manager.clear_conversation(user_id)
    return jsonify({'status': 'success', 'message': 'Conversation cleared'}), 200


@api.route('agent-action', methods = ['POST'])
def agent_action():
    "API to test the action agent"

    data = request.json
    user_id = data.get("user_id", "default")
    query = data.get("query")

    if not data or 'query' not in data:
        return Response(
            json.dumps({'error': 'Query is required'}, ensure_ascii=False),
            content_type="application/json; charset=utf-8",
            status=400
        )


    try:
        result = agent.handle_action(query, user_id)
        history = agent.conversation_manager.get_conversation(user_id)

        return Response(
            json.dumps({
                "user_id": user_id,
                "response": result,
                "conversation_history": history
            }, ensure_ascii=False),
            content_type="application/json; charset=utf-8",
            status=200
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

    
# -- FULL PIPELINE API