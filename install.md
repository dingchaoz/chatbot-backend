# humana real world chatbot backend

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
