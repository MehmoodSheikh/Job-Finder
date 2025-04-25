"""
Relevance filtering service using scikit-learn and nltk
"""
import re
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from typing import List, Dict, Any

from app.models.job import Job, JobRequest

# Ensure NLTK resources are available
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')
    nltk.download('wordnet')


class RelevanceFilteringService:
    """
    Service for filtering jobs based on relevance to the search criteria
    """
    
    def __init__(self):
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words('english'))
        self.vectorizer = TfidfVectorizer()
    
    def filter_jobs_by_relevance(self, jobs: List[Job], job_request: JobRequest, threshold: float = 0.2) -> List[Job]:
        """
        Filter jobs based on relevance to the search criteria
        
        Args:
            jobs: List of jobs to filter
            job_request: The job search criteria
            threshold: Minimum relevance score threshold (0-1)
            
        Returns:
            List of relevant jobs sorted by relevance score
        """
        if not jobs:
            return []
        
        # Create a query document from the job request
        query_doc = self._create_query_document(job_request)
        
        # Create job documents
        job_docs = [self._create_job_document(job) for job in jobs]
        
        # Calculate relevance scores
        relevance_scores = self._calculate_relevance_scores(query_doc, job_docs)
        
        # Filter and sort jobs by relevance score
        relevant_jobs = []
        for i, score in enumerate(relevance_scores):
            if score >= threshold:
                jobs[i].relevance_score = float(score)  # Add relevance score to job
                relevant_jobs.append(jobs[i])
        
        # Sort by relevance score (descending)
        relevant_jobs.sort(key=lambda x: getattr(x, 'relevance_score', 0), reverse=True)
        
        return relevant_jobs
    
    def _preprocess_text(self, text: str) -> str:
        """
        Preprocess text for relevance calculation
        
        Args:
            text: Text to preprocess
            
        Returns:
            Preprocessed text
        """
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove special characters and numbers
        text = re.sub(r'[^a-zA-Z\s]', '', text)
        
        # Tokenize
        tokens = word_tokenize(text)
        
        # Remove stop words and lemmatize
        tokens = [self.lemmatizer.lemmatize(token) for token in tokens if token not in self.stop_words]
        
        return ' '.join(tokens)
    
    def _create_query_document(self, job_request: JobRequest) -> str:
        """
        Create a document from the job request for relevance calculation
        
        Args:
            job_request: The job search criteria
            
        Returns:
            Preprocessed document
        """
        # Combine all relevant fields from the job request
        query_parts = [
            job_request.position,
            job_request.skills or "",
            job_request.location or "",
            job_request.jobNature or "",
            job_request.experience or ""
        ]
        
        # Join and preprocess
        query_text = ' '.join(filter(None, query_parts))
        return self._preprocess_text(query_text)
    
    def _create_job_document(self, job: Job) -> str:
        """
        Create a document from a job for relevance calculation
        
        Args:
            job: Job to create document from
            
        Returns:
            Preprocessed document
        """
        # Combine all relevant fields from the job
        job_parts = [
            job.job_title,
            job.company,
            job.location or "",
            job.jobNature or "",
            job.experience or "",
            job.description or ""
        ]
        
        # Join and preprocess
        job_text = ' '.join(filter(None, job_parts))
        return self._preprocess_text(job_text)
    
    def _calculate_relevance_scores(self, query_doc: str, job_docs: List[str]) -> List[float]:
        """
        Calculate relevance scores between query and job documents
        
        Args:
            query_doc: Preprocessed query document
            job_docs: List of preprocessed job documents
            
        Returns:
            List of relevance scores
        """
        # Combine query and job documents
        all_docs = [query_doc] + job_docs
        
        # Vectorize documents
        tfidf_matrix = self.vectorizer.fit_transform(all_docs)
        
        # Calculate cosine similarity between query and each job
        query_vector = tfidf_matrix[0:1]
        job_vectors = tfidf_matrix[1:]
        
        # Calculate cosine similarity
        similarity_scores = cosine_similarity(query_vector, job_vectors).flatten()
        
        return similarity_scores
