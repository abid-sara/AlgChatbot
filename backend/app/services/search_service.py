import json
import logging
import os
import numpy as np
import faiss
import pickle
from app.utils.vectorizer import HybridVectorizer
from rank_bm25 import BM25Okapi
from config.settings import DATA_PATH, TOP_N_RESULTS, DEFAULT_SEARCH_METHOD, VECTOR_DB_PATH

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SearchService:
    def __init__(self, embedding_model="intfloat/multilingual-e5-base",
                 tfidf_weight=0.3, bm25_weight=0.3, embedding_weight=0.4,
                 search_method=None):
       
        os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
        os.makedirs(os.path.dirname(VECTOR_DB_PATH), exist_ok=True)

        self.search_method = search_method or DEFAULT_SEARCH_METHOD
        logger.info(f"Initializing SearchService with search method: {self.search_method}")

        self.vectorizer = HybridVectorizer(embedding_model=embedding_model)
        self.vectorizer.set_weights(
            tfidf_weight=tfidf_weight,
            bm25_weight=bm25_weight,
            embedding_weight=embedding_weight
        )
        self.chunks = []
        self.vector_index = None
        self.is_fitted = False

        # Load existing data if available
        self.load_data()

    def load_data(self):
        """Load document chunks from JSON file and vector database"""
        try:
            if not os.path.exists(DATA_PATH):
                logger.warning(f"Data file {DATA_PATH} does not exist.")
                self.chunks = []
                return False

            # Load plain string chunks
            with open(DATA_PATH, 'r', encoding='utf-8') as file:
                self.chunks = json.load(file)

            if not self.chunks:
                logger.warning("No chunks found in data file")
                return False

            logger.info(f"Loaded {len(self.chunks)} chunks from {DATA_PATH}")

            if os.path.exists(VECTOR_DB_PATH) and os.path.exists(f"{VECTOR_DB_PATH}.meta"):
                success = self._load_vector_db()
                if not success:
                    success = self._build_vector_db()
            else:
                success = self._build_vector_db()

            self.is_fitted = success
            return success

        except Exception as e:
            logger.error(f"Error loading chunks: {e}")
            self.chunks = []
            self.is_fitted = False
            return False

    def _load_vector_db(self):
        """Load FAISS index and metadata"""
        try:
            self.vector_index = faiss.read_index(VECTOR_DB_PATH)
            with open(f"{VECTOR_DB_PATH}.meta", 'rb') as f:
                metadata = pickle.load(f)

            self.vectorizer.tfidf_vectorizer = metadata.get('tfidf_vectorizer')
            self.vectorizer.tfidf_vectors = metadata.get('tfidf_vectors')
            self.vectorizer.bm25 = metadata.get('bm25')
            self.vectorizer.tokenized_chunks = metadata.get('tokenized_chunks', [])
            self.vectorizer.preprocessed_chunks = metadata.get('preprocessed_chunks', [])
            self.vectorizer.embedding_vectors = metadata.get('embedding_vectors')

            self.vectorizer.chunks = self.chunks
            self.vectorizer.is_fitted = True

            if self.vector_index.ntotal != len(self.chunks):
                logger.warning("Vector index size doesn't match chunk count. Rebuilding.")
                return self._build_vector_db()

            logger.info(f"Loaded vector DB with {self.vector_index.ntotal} vectors")
            return True
        except Exception as e:
            logger.error(f"Error loading vector DB: {e}")
            return False

    def _build_vector_db(self):
        """Build vector DB from scratch"""
        logger.info("Building vector DB from chunks...")

        if not self.chunks:
            return False

        success = self.vectorizer.fit(self.chunks)
        if not success or self.vectorizer.embedding_vectors is None:
            return False

        embedding_dim = self.vectorizer.embedding_vectors.shape[1]
        self.vector_index = faiss.IndexFlatL2(embedding_dim)
        vectors = np.array(self.vectorizer.embedding_vectors).astype('float32')
        self.vector_index.add(vectors)

        self._save_vector_db()
        logger.info(f"Built vector DB with {len(self.chunks)} chunks")
        return True

    def _save_vector_db(self):
        """Save FAISS index + metadata"""
        try:
            faiss.write_index(self.vector_index, VECTOR_DB_PATH)
            metadata = {
                'tfidf_vectorizer': self.vectorizer.tfidf_vectorizer,
                'tfidf_vectors': self.vectorizer.tfidf_vectors,
                'bm25': self.vectorizer.bm25,
                'tokenized_chunks': self.vectorizer.tokenized_chunks,
                'preprocessed_chunks': self.vectorizer.preprocessed_chunks,
                'embedding_vectors': self.vectorizer.embedding_vectors,
                'last_updated': np.datetime64('now')
            }
            with open(f"{VECTOR_DB_PATH}.meta", 'wb') as f:
                pickle.dump(metadata, f)
            return True
        except Exception as e:
            logger.error(f"Error saving vector DB: {e}")
            return False

    def add_documents(self, new_chunks):
        """Add new string chunks to DB"""
        if not new_chunks:
            return False

        try:
            if not self.is_fitted:
                self.chunks.extend(new_chunks)
                return self._build_vector_db()

            self.chunks.extend(new_chunks)

            tokenized_new, preprocessed_new = [], []
            for chunk in new_chunks:
                tokens, preprocessed = self.vectorizer.preprocess_text(chunk)
                tokenized_new.append(tokens)
                preprocessed_new.append(preprocessed)

            self.vectorizer.tokenized_chunks.extend(tokenized_new)
            self.vectorizer.preprocessed_chunks.extend(preprocessed_new)

            new_embeddings = self.vectorizer.get_embeddings([f"passage: {p}" for p in preprocessed_new] )
            if new_embeddings is not None:
                self.vector_index.add(np.array(new_embeddings).astype('float32'))
                self.vectorizer.embedding_vectors = np.vstack([
                    self.vectorizer.embedding_vectors,
                    new_embeddings
                ])

            # Update TF-IDF & BM25
            self.vectorizer.tfidf_vectors = self.vectorizer.tfidf_vectorizer.fit_transform(
                self.vectorizer.preprocessed_chunks
            )
            self.vectorizer.bm25 = BM25Okapi(self.vectorizer.tokenized_chunks)

            # Save updated DB
            with open(DATA_PATH, 'w', encoding='utf-8') as f:
                json.dump(self.chunks, f, ensure_ascii=False)
            self._save_vector_db()

            return True
        except Exception as e:
            logger.error(f"Error adding documents: {e}")
            return False

    def search(self, query, top_n=10, search_method='hybrid'):
        """Search chunks by query"""
        results = []
        if not self.is_fitted or not self.chunks:
            return []

        method = search_method or self.search_method
        if method == 'embeddings':
            results =  self._vector_search(query, top_n)
        else:
            results = self.vectorizer.search(query, top_n, method=method)
        
        # Re-rank hybrid to work well when question is in a language and chunk in another since tf-idf and bm25 don't
        if method == "hybrid" and results:
            results = self._rerank_with_embeddings(query, results)
        
        return results
    

    def _vector_search(self, query, top_n):
        """Direct FAISS vector search"""
        if not self.vector_index or self.vector_index.ntotal == 0:
            return []

        _, preprocessed_query = self.vectorizer.preprocess_text(query)
        query_embedding = self.vectorizer.get_embeddings([f"query: {preprocessed_query}"])
        if query_embedding is None:
            return []

        query_vector = query_embedding[0].reshape(1, -1).astype('float32')
        distances, indices = self.vector_index.search(query_vector, k=min(top_n, self.vector_index.ntotal))

        results = []
        for i, idx in enumerate(indices[0]):
            if idx != -1 and idx < len(self.chunks):
                similarity = 1.0 / (1.0 + distances[0][i])
                results.append((self.chunks[idx], float(similarity)))
        return results

    def _rerank_with_embeddings(self, query, results):
        """
        Re-rank search results using FAISS embeddings-only similarity.
        Much faster than recomputing embeddings for each chunk.
        """
        if not results or not self.vector_index or self.vector_index.ntotal == 0:
            return results

        # Preprocess query
        _, preprocessed_query = self.vectorizer.preprocess_text(query)

        # Get query embedding
        query_embedding = self.vectorizer.get_embeddings([f"query: {preprocessed_query}"])
        if query_embedding is None or len(query_embedding) == 0:
            return results

        query_vec = query_embedding.astype("float32")

        # Search in FAISS for the top matches
        distances, indices = self.vector_index.search(query_vec, k=len(results))

        reranked = []
        for rank, idx in enumerate(indices[0]):
            if idx != -1 and idx < len(self.chunks):
                similarity = 1.0 / (1.0 + distances[0][rank])  # convert L2 to similarity
                reranked.append((self.chunks[idx], float(similarity)))

        return reranked


    def format_search_results(self, results):
        """Format results for chatbot"""
        return [f"{i+1}. {chunk}" for i, (chunk, _) in enumerate(results)]
