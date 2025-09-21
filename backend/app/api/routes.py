import json
import logging
from flask import Blueprint, request, jsonify, Response
from werkzeug.exceptions import BadRequestKeyError, RequestEntityTooLarge

from app.services.search_service import SearchService
from app.utils.docx_processor import DocxProcessor


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


# ------------------- Config -------------------
@api.route('/config', methods=['GET'])
def get_config():
    return jsonify({
        'weights': search_service.vectorizer.weights,
        'embedding_model': EMBEDDING_MODEL,
        'search_method': search_service.search_method,
        'available_methods': ['hybrid', 'tfidf', 'bm25', 'embeddings']
    }), 200

@api.route('/config', methods=['POST'])
def update_config():
    data = request.json
    if not data:
        return jsonify({'error': 'No configuration data provided'}), 400

    search_method = data.get('search_method')
    if search_method:
        search_service.set_search_method(search_method)

    weights = data.get('weights', {})
    if weights:
        search_service.vectorizer.set_weights(
            tfidf_weight=weights.get('tfidf', search_service.vectorizer.weights['tfidf']),
            bm25_weight=weights.get('bm25', search_service.vectorizer.weights['bm25']),
            embedding_weight=weights.get('embeddings', search_service.vectorizer.weights['embeddings'])
        )

    return jsonify({
        'weights': search_service.vectorizer.weights,
        'search_method': search_service.search_method,
        'status': 'updated'
    }), 200
