"""
Script to download required NLTK data
"""
import nltk

def download_nltk_data():
    """Download required NLTK data packages"""
    nltk_packages = [
        'punkt',
        'stopwords',
        'wordnet'
    ]
    
    for package in nltk_packages:
        print(f"Downloading NLTK package: {package}")
        nltk.download(package)
    
    print("NLTK setup complete.")

if __name__ == "__main__":
    download_nltk_data()