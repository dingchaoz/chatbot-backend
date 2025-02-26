# Chatbot real world backend

## **Setup and Execution Guide**

### 1. Synchronize Dependencies
Run the following command to sync project dependencies:
```bash
uv sync
```
### 2. Activate Virtual Environment
Activate the virtual environment to ensure dependencies are installed correctly:
```bash
source .venv/bin/activate
```

### 3. Configure Environment Variables
Edit the `.env` file to set necessary environment variables:
```bash
vim .env
```

### 4. Start Local Database
Run the local database using Docker Compose:
```bash
docker compose -f docker-compose.local.yaml up -d
```

### 5. Preprocess Database
Execute the preprocessing script to prepare the database:
```bash
bash ./scripts/prestart.sh
```

### 6. Preprocess PDF Files
Run the preprocessing script for handling PDF files:
```bash
python preprocess.py
```

### 7. Start FastAPI Application
Launch the FastAPI application with hot-reloading enabled:
```bash
fastapi run --reload app/main.py
```

## TODO

- pass embed model into vector db indexer
- use sentence splitter, define overlap, chunk size
- use low level index by creating node, parsers and node id and have response include th node id and text
- use low level retriever, query engine by defining similarity score, etc
- use llama indexer evalution and ragas together, retriever evaluation will use sythentic dataset to generate offline eval dataset, and for online we will use faithfullness and query/ sythentic generation for generate online evaluation,
- create seperate script for online and offline eval; for offline eval, create a report,
- for online, append and add to a csv or other file to save and report online eval, and add a dashbaord to include it later, if time allowes,
- if time further allows, look into the eval part to use localhost arize and other dashboard to allow for human feedback and other dashborad to be seen, see llamaindex document
- manually use open ai to interprete chart tables into text and append them into text embedding
- use open source multi modal llm e.g. qwen vl model?  to do the above step
