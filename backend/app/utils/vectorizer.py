from sklearn.feature_extraction.text import TfidfVectorizer
from rank_bm25 import BM25Okapi
from transformers import AutoTokenizer, AutoModel
import torch
import numpy as np
import logging
import re
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from langdetect import detect, DetectorFactory
DetectorFactory.seed = 0  # make detection deterministic

logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class HybridVectorizer:
    def __init__(self, embedding_model="jinaai/jina-embeddings-v3"):
        """
        Initialize the hybrid vectorizer with TF-IDF, BM25, and Hugging Face embeddings
        """
        # NLTK setup
        nltk.download('punkt', quiet=True)
        nltk.download('stopwords', quiet=True)

        self.arabic_stopwords = set(stopwords.words('arabic') if 'arabic' in stopwords._fileids else [])
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

        # Initialize TF-IDF
        self.tfidf_vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            min_df=2,
            max_df=0.85,
            sublinear_tf=True
        )

        # BM25 placeholder
        self.bm25 = None

        # Load embedding model
        try:
            logger.info(f"Loading embedding model: {embedding_model}")
            self.tokenizer = AutoTokenizer.from_pretrained(embedding_model, trust_remote_code=True)
            self.model = AutoModel.from_pretrained(embedding_model, trust_remote_code=True).to(self.device)
            self.model.eval()
            logger.info(f"Embedding model loaded on {self.device}")
        except Exception as e:
            logger.error(f"Error loading embedding model: {e}")
            self.tokenizer, self.model = None, None

        # Storage
        self.chunks = []
        self.preprocessed_chunks = []
        self.tokenized_chunks = []
        self.tfidf_vectors = None
        self.embedding_vectors = None
        self.is_fitted = False

        # Weights
        self.weights = {
            'tfidf': 0.3,
            'bm25': 0.3,
            'embeddings': 0.4
        }


    def preprocess_text(self, text: str):
        """
        Preprocess text based on detected language.
        Arabic → special Arabic cleaning
        Other languages → light preprocessing
        """
        try:
            lang = detect(text)
        except:
            lang = "unknown"

        if lang == "ar":
            return self.preprocess_arabic_text(text)
        else:
            return self.preprocess_non_arabic_text(text)

    def preprocess_non_arabic_text(self, text: str):
        text = text.lower()
        text = re.sub(r"[^a-z0-9\s]", " ", text)  # keep only alphanumerics + spaces
        text = re.sub(r"\s+", " ", text).strip()
        tokens = text.split()
        return tokens, text


    def normalize_arabic_text(self, text):
        text = re.sub(r'[\u064B-\u065F\u0670]', '', text)  # Remove diacritics
        text = re.sub(r'[^\u0600-\u06FF\s0-9a-zA-Z]', ' ', text)  # Keep Arabic/Latin/numbers
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def preprocess_arabic_text(self, text):
        text = self.normalize_arabic_text(text)
        tokens = word_tokenize(text)
        tokens = [t for t in tokens if t not in self.arabic_stopwords]
        return tokens, ' '.join(tokens)

    def _mean_pooling(self, model_output, attention_mask):
        """Mean pooling for sentence embeddings"""
        token_embeddings = model_output.last_hidden_state
        mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        return (token_embeddings * mask_expanded).sum(1) / mask_expanded.sum(1)

    def get_embeddings(self, texts):
        if self.model is None or self.tokenizer is None:
            return None

        all_embeddings = []
        batch_size = 8
        with torch.no_grad():
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i+batch_size]
                encoded = self.tokenizer(
                    batch, padding=True, truncation=True,
                    max_length=512, return_tensors="pt"
                ).to(self.device)

                outputs = self.model(**encoded)
                embeddings = self._mean_pooling(outputs, encoded['attention_mask'])
                all_embeddings.extend(embeddings.cpu().numpy())

        return np.array(all_embeddings)

    
    def fit(self, chunks):
        """Fit the hybrid vectorizer on document chunks"""
        # Handle case where chunks is None or empty
        if not chunks:
            logger.warning("No document chunks provided to fit. Vectorizer remains unfitted.")
            self.is_fitted = False
            return False
            
        self.chunks = chunks
        
        # Preprocess chunks
        tokenized_chunks = []
        preprocessed_chunks = []
        
        for chunk in chunks:
            tokens, preprocessed = self.preprocess_text(chunk)
            tokenized_chunks.append(tokens)
            preprocessed_chunks.append(preprocessed)
        
        self.tokenized_chunks = tokenized_chunks
        self.preprocessed_chunks = preprocessed_chunks
        
        try:
            # Handle edge case for TF-IDF with only one document
            if len(chunks) == 1:
                logger.warning("Only one document provided. Using simplified TF-IDF.")
                self.tfidf_vectorizer = TfidfVectorizer(min_df=1, max_df=1.0)
                
            # Fit TF-IDF
            self.tfidf_vectors = self.tfidf_vectorizer.fit_transform(preprocessed_chunks)
            logger.info(f"TF-IDF vectorizer fitted on {len(chunks)} chunks")
            
            # Initialize BM25
            self.bm25 = BM25Okapi(tokenized_chunks)
            logger.info("BM25 model initialized")
            
            # Generate embeddings
            if self.model is not None:
                logger.info("Generating embeddings for document chunks...")
                self.embedding_vectors = self.get_embeddings(preprocessed_chunks)
                logger.info(f"Generated embeddings with shape: {self.embedding_vectors.shape}")
            else:
                logger.warning("Embedding model not available, will rely on TF-IDF and BM25 only")
            
            # Set fitted flag to True
            self.is_fitted = True
            return True
        except Exception as e:
            logger.error(f"Error during vectorizer fitting: {e}")
            self.is_fitted = False
            return False
    
    def set_weights(self, tfidf_weight=0.3, bm25_weight=0.3, embedding_weight=0.4):
        """Set weights for hybrid search components"""
        self.weights = {
            'tfidf': tfidf_weight,
            'bm25': bm25_weight,
            'embeddings': embedding_weight
        }
        
        # Normalize weights to sum to 1
        weight_sum = sum(self.weights.values())
        for key in self.weights:
            self.weights[key] /= weight_sum
        
        logger.info(f"Search weights set to: {self.weights}")
    

    def search(self, query, top_n=10, method='hybrid'):
        """
        Search for relevant documents using specified search method
        
        Args:
            query (str): The search query
            top_n (int): Number of results to return
            method (str): Search method to use ('hybrid', 'tfidf', 'bm25', 'embeddings')
        """
        valid_methods = ['hybrid', 'tfidf', 'bm25', 'embeddings']
        if method not in valid_methods:
            logger.warning(f"Invalid search method: {method}. Using 'hybrid' instead.")
            method = 'hybrid'
            
        # Check if vectorizer has been fitted
        if not self.is_fitted:
            logger.warning("Vectorizer hasn't been fitted with documents yet. Returning empty results.")
            return []  # Return empty list instead of raising exception
        else :
            logger.info("Using fitted vectorizer for search")
            
        # Check if we have documents to search
        if not self.chunks:
            logger.warning("No documents to search. Returning empty results.")
            return []
        
        # Preprocess query
        query_tokens, preprocessed_query = self.preprocess_text(query)
        
        # Get scores based on method
        if method == 'tfidf':
            return self._tfidf_search(preprocessed_query, top_n)
        elif method == 'bm25':
            return self._bm25_search(query_tokens, top_n)
        elif method == 'embeddings':
            return self._embedding_search(preprocessed_query, top_n)
        else:  # hybrid (default)
            return self._hybrid_search(query_tokens, preprocessed_query, top_n)
    
    def _tfidf_search(self, preprocessed_query, top_n):
        """Search using TF-IDF only"""
        # Safety check
        if self.tfidf_vectors is None or not self.is_fitted:
            logger.warning("TF-IDF vectors not available. Returning empty results.")
            return []
            
        # TF-IDF scoring
        try:
            tfidf_query_vector = self.tfidf_vectorizer.transform([preprocessed_query])
            tfidf_scores = np.asarray(tfidf_query_vector.dot(self.tfidf_vectors.T).toarray())[0]
            
            # Combine chunks with scores and sort
            chunk_score_pairs = list(zip(self.chunks, tfidf_scores.tolist()))
            ranked_chunks = sorted(chunk_score_pairs, key=lambda x: x[1], reverse=True)
            
            # Return top N results
            return ranked_chunks[:top_n]
        except Exception as e:
            logger.error(f"Error in TF-IDF search: {e}")
            return []
    
    def _bm25_search(self, query_tokens, top_n):
        """Search using BM25 only"""
        # Safety check
        if self.bm25 is None or not self.is_fitted:
            logger.warning("BM25 model not available. Returning empty results.")
            return []
            
        try:
            # BM25 scoring
            bm25_scores = np.array(self.bm25.get_scores(query_tokens))
            
            # Combine chunks with scores and sort
            chunk_score_pairs = list(zip(self.chunks, bm25_scores.tolist()))
            ranked_chunks = sorted(chunk_score_pairs, key=lambda x: x[1], reverse=True)
            
            # Return top N results
            return ranked_chunks[:top_n]
        except Exception as e:
            logger.error(f"Error in BM25 search: {e}")
            return []
    
    def _embedding_search(self, preprocessed_query, top_n):
        """Search using embeddings only"""
        if self.model is None or self.embedding_vectors is None or not self.is_fitted:
            logger.warning("Embedding model or vectors not available. Falling back to TF-IDF.")
            return self._tfidf_search(preprocessed_query, top_n)
        
        try:
            # Generate query embedding
            query_embedding = self.get_embeddings([preprocessed_query])[0]
            
            # Calculate cosine similarity
            similarity = torch.nn.functional.cosine_similarity(
                torch.tensor(query_embedding).unsqueeze(0),
                torch.tensor(self.embedding_vectors),
                dim=1
            ).numpy()
            
            # Combine chunks with scores and sort
            chunk_score_pairs = list(zip(self.chunks, similarity.tolist()))
            ranked_chunks = sorted(chunk_score_pairs, key=lambda x: x[1], reverse=True)
            
            # Return top N results
            return ranked_chunks[:top_n]
        except Exception as e:
            logger.error(f"Error in embedding search: {e}")
            return self._tfidf_search(preprocessed_query, top_n)  # Fallback
    
    def _hybrid_search(self, query_tokens, preprocessed_query, top_n):
        """
        Search for relevant documents using hybrid approach combining
        TF-IDF, BM25, and embeddings
        """
        # Safety check
        if not self.is_fitted:
            logger.warning("Vectorizer not fitted. Returning empty results.")
            return []
            
        try:
            # --- TF-IDF scoring ---
            tfidf_scores = np.zeros(len(self.chunks))
            if self.tfidf_vectors is not None:
                tfidf_query_vector = self.tfidf_vectorizer.transform([preprocessed_query])
                tfidf_scores = np.asarray(tfidf_query_vector.dot(self.tfidf_vectors.T).toarray())[0]
                
                # Normalize TF-IDF scores
                tfidf_max = np.max(tfidf_scores) if np.max(tfidf_scores) > 0 else 1
                tfidf_scores = tfidf_scores / tfidf_max
            
            # --- BM25 scoring ---
            bm25_scores = np.zeros(len(self.chunks))
            if self.bm25 is not None:
                bm25_scores = np.array(self.bm25.get_scores(query_tokens))
                
                # Normalize BM25 scores
                bm25_max = np.max(bm25_scores) if np.max(bm25_scores) > 0 else 1
                bm25_scores = bm25_scores / bm25_max
            
            # --- Embedding similarity scoring ---
            embedding_scores = np.zeros(len(self.chunks))
            if self.model is not None and self.embedding_vectors is not None:
                query_embedding = self.get_embeddings([preprocessed_query])[0]
                
                # Calculate cosine similarity between query and document embeddings
                similarity = torch.nn.functional.cosine_similarity(
                    torch.tensor(query_embedding).unsqueeze(0),
                    torch.tensor(self.embedding_vectors),
                    dim=1
                ).numpy()
                
                embedding_scores = (similarity + 1) / 2  # Normalize from [-1,1] to [0,1]
            
            # --- Exact match and term match bonuses ---
            exact_match_scores = np.zeros(len(self.chunks))
            for i, chunk in enumerate(self.preprocessed_chunks):
                # Bonus for exact phrase match
                if preprocessed_query in chunk:
                    exact_match_scores[i] += 0.3
                
                # Count term matches and add proportional bonus
                term_matches = sum(1 for term in query_tokens if term in self.tokenized_chunks[i])
                term_match_ratio = term_matches / len(query_tokens) if query_tokens else 0
                exact_match_scores[i] += term_match_ratio * 0.2
            
            # --- Combine scores with configured weights ---
            combined_scores = (
                self.weights['tfidf'] * tfidf_scores +
                self.weights['bm25'] * bm25_scores +
                self.weights['embeddings'] * embedding_scores +
                0.2 * exact_match_scores  # 20% weight for exact matches
            )
            
            # Combine chunks with scores and sort
            chunk_score_pairs = list(zip(self.chunks, combined_scores.tolist()))
            ranked_chunks = sorted(chunk_score_pairs, key=lambda x: x[1], reverse=True)
            
            # Return top N results
            return ranked_chunks[:top_n]
        except Exception as e:
            logger.error(f"Error in hybrid search: {e}. Returning empty results.")
            return []