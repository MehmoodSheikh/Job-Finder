"""
Download NLTK resources script
"""
import nltk

# Download necessary NLTK resources
print("Downloading NLTK resources...")
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')
print("NLTK resources downloaded successfully.")
