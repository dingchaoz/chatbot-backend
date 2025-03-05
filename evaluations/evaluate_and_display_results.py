import os
import pandas as pd
import asyncio
import pickle
from dotenv import load_dotenv
from llama_index.core.evaluation import RetrieverEvaluator
from llama_index.core.retrievers import VectorIndexRetriever

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

# Load the testset
current_folder = os.path.dirname(os.path.abspath(__file__))
csv_file_path = os.path.join(current_folder, "llamaindextestset.csv")
qa_dataset = pd.read_csv(csv_file_path)

def display_results(name, eval_results):
    """Display results from evaluate."""
    metric_dicts = []
    for eval_result in eval_results:
        metric_dict = eval_result.metric_vals_dict
        metric_dicts.append(metric_dict)

    full_df = pd.DataFrame(metric_dicts)

    columns = {
        "retrievers": [name],
        **{k: [full_df[k].mean()] for k in metrics},
    }

    metric_df = pd.DataFrame(columns)

    return metric_df

async def main():
    eval_results = await retriever_evaluator.aevaluate_dataset(qa_dataset)
    print(eval_results)
    display_results("top-2 eval", eval_results)
    df = pd.DataFrame(eval_results)
    print("df is", df)
    df.to_csv("llamaindextestset.csv", index=False)


asyncio.run(main())