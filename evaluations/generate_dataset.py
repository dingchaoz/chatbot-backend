import os
import pandas as pd
import pickle
from dotenv import load_dotenv
from llama_index.core.evaluation import generate_question_context_pairs
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.evaluation import RetrieverEvaluator

# Load environment variables from .env file
load_dotenv()

# Set OpenAI API key
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError("OPENAI_API_KEY not found in environment variables")
os.environ["OPENAI_API_KEY"] = openai_api_key

# Load preprocessed data and index during startup
artifacts_dir = os.path.join(os.path.dirname(__file__), '..', 'artifacts')
try:
    with open(os.path.join(artifacts_dir, "index.pkl"), "rb") as f:
        index = pickle.load(f)
    with open(os.path.join(artifacts_dir, "llm.pkl"), "rb") as f:
        llm = pickle.load(f)
    with open(os.path.join(artifacts_dir, "nodes.pkl"), "rb") as f:
        nodes = pickle.load(f)

    retriever = VectorIndexRetriever(
        index=index,
        similarity_top_k=5,
    )

except (FileNotFoundError, pickle.UnpicklingError) as e:
    raise RuntimeError("Failed to load preprocessed data and index") from e

metrics = ["hit_rate", "mrr", "precision", "recall", "ap", "ndcg"]

retriever_evaluator = RetrieverEvaluator.from_metric_names(
    metrics, retriever=retriever
)

qa_dataset = generate_question_context_pairs(
    nodes, llm=llm, num_questions_per_chunk=2
)

# Save the dataset to a CSV file in the evaluations folder
current_folder = os.path.dirname(os.path.abspath(__file__))
csv_file_path = os.path.join(current_folder, "llamaindextestset.csv")
qa_dataset.to_csv(csv_file_path, index=False)

print(f"Dataset saved to {csv_file_path}")