import sentry_sdk
from fastapi import FastAPI
from fastapi.routing import APIRoute
from starlette.middleware.cors import CORSMiddleware
import pickle
from contextlib import asynccontextmanager
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.response_synthesizers import get_response_synthesizer
from llama_index.core.postprocessor import SimilarityPostprocessor
from llama_index.core.prompts import PromptTemplate
import os

from app.api.router import api_router
from app.core.config import settings

def custom_generate_unique_id(route: APIRoute) -> str:
    return f"{route.tags[0]}-{route.name}"

def initialize_retriever(index, similarity_top_k=5):
    return VectorIndexRetriever(
        index=index,
        similarity_top_k=similarity_top_k,
    )

def initialize_synthesizer(llm):
    qa_prompt_tmpl = (
        "You are a helpful assistant. Below is some context retrieved from documents, followed by the chat history. "
        "Please respond to the user's message using the provided context. Format your response as bullet points, "
        "and after each statement, reference the original sentence from the context that supports it by saying (Ref: sentence).\n\n"
        "Context:\n"
        "---------------------\n"
        "{context_str}\n"
        "---------------------\n"
        "Given the context information and not prior knowledge, "
        "answer the query.\n"
        "Query: {query_str}\n"
        "Answer: "
    )
    qa_prompt = PromptTemplate(qa_prompt_tmpl)
    return get_response_synthesizer(llm=llm, streaming=True, text_qa_template=qa_prompt)

def initialize_query_engine(retriever, synthesizer):
    return RetrieverQueryEngine(
        retriever=retriever,
        response_synthesizer=synthesizer,
        node_postprocessors=[SimilarityPostprocessor(similarity_cutoff=0.7)],
    )

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load preprocessed data and index during startup
    artifacts_dir = os.path.join(os.path.dirname(__file__), '..', 'artifacts')
    try:
        with open(os.path.join(artifacts_dir, "index.pkl"), "rb") as f:
            app.state.index = pickle.load(f)
        with open(os.path.join(artifacts_dir, "llm.pkl"), "rb") as f:
            app.state.llm = pickle.load(f)

        # Initialize retriever, synthesizer, and query engine
        app.state.retriever = initialize_retriever(app.state.index)
        app.state.synthesizer = initialize_synthesizer(app.state.llm)
        app.state.query_engine = initialize_query_engine(app.state.retriever, app.state.synthesizer)

    except (FileNotFoundError, pickle.UnpicklingError) as e:
        raise RuntimeError("Failed to load preprocessed data and index") from e

    yield
    # Perform any necessary cleanup during shutdown

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    generate_unique_id_function=custom_generate_unique_id,
    lifespan=lifespan,
)

# Set all CORS enabled origins
if settings.all_cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.all_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router)
