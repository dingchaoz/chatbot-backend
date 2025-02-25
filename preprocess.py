from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, Settings as LlamaSettings
from llama_index.llms.deepseek import DeepSeek
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.node_parser import SemanticSplitterNodeParser
from llama_index.core.base.embeddings.base import BaseEmbedding
from app.core.config import settings
import pickle
import os
import re


def clean_text(text):
    """
    Clean the extracted text by removing headers, page numbers, and references.
    """
    # Remove headers like "BIOM 255 (Leffert) - Discussion Feb. 1, 2007"
    text = re.sub(r'BIOM 255 \(Leffert\) - Discussion Feb\. 1, 2007', '', text)
    
    # Remove page numbers (e.g., "Page 1 of 10" if present)
    text = re.sub(r'Page \d+ of \d+', '', text)
    
    # Remove lines that are entirely in uppercase (likely headers)
    text = re.sub(r'^[A-Z\s]+$', '', text, flags=re.MULTILINE)
    
    # Remove references section (heuristic: starts with "REFERENCES AND NOTES")
    text = re.split(r'\nREFERENCES AND NOTES\n', text)[0]
    
    # Remove extra whitespace and empty lines
    text = re.sub(r'\n+', '\n', text).strip()
    
    return text

def preprocess_data():
    llm = DeepSeek(
        model=settings.DEEPSEEK_MODEL_NAME,
        api_key=settings.DEEPSEEK_API_KEY,
        api_base=settings.DEEPSEEK_API_BASE
    )
    LlamaSettings.embed_model = HuggingFaceEmbedding(
        model_name=settings.HUGGING_FACE_EMBEDDING_MODEL_NAME
    )

    reader = SimpleDirectoryReader(input_files=[settings.PDF_FILE_PATH])
    data = reader.load_data()

    # Clean the text of each document and create new Document objects
    cleaned_data = []
    for doc in data:
        cleaned_text = clean_text(doc.text)
        cleaned_doc = doc.copy(update={"text": cleaned_text})
        cleaned_data.append(cleaned_doc)
    
    
    # Initialize Semantic Splitter Node Parser
    parser = SemanticSplitterNodeParser(
        embed_model=LlamaSettings.embed_model,   # Embedding model for similarity-based chunking
        breakpoint_percentile_threshold=95,  # Adjust to control chunk granularity
        buffer_size=1  # Context buffer (adjust based on needs)
    )

    # Parse Documents into Semantic Nodes
    nodes = parser.get_nodes_from_documents(cleaned_data)


    # Create the vector store index
    index = VectorStoreIndex(
        nodes=nodes,
    )

    # Ensure the artifacts directory exists
    artifacts_dir = os.path.join(os.path.dirname(__file__), 'artifacts')
    os.makedirs(artifacts_dir, exist_ok=True)

    # Save the index and llm objects to the artifacts directory
    with open(os.path.join(artifacts_dir, "index.pkl"), "wb") as f:
        pickle.dump(index, f)

    with open(os.path.join(artifacts_dir, "llm.pkl"), "wb") as f:
        pickle.dump(llm, f)

if __name__ == "__main__":
    preprocess_data()