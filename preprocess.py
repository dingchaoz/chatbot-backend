from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, Settings as LlamaSettings
from llama_index.llms.deepseek import DeepSeek
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from app.core.config import settings
import pickle
import os

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

    index = VectorStoreIndex.from_documents(documents=data, show_progress=True)

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