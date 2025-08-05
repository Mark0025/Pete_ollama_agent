---

## 2025-08-05 – Local-first FastAPI refactor

### What’s new

| Area                | Status                                                                                                                       |
| ------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| **FastAPI server**  | ✅ Runs head-less (`src/main.py` launches `VAPIWebhookServer`).                                                              |
| `/ui` playground    | ✅ Persona selector (icons) and streaming chat.                                                                              |
| `/admin` dashboard  | ✅ Load samples & one-click “Train Property-Manager Model”.                                                                  |
| **Data extraction** | ✅ `src/virtual_jamie_extractor.py` connects to prod SQL Server (needs `PROD_DB_*` env vars) → builds `/app/pete.db`.        |
| **Fine-tuning**     | ✅ `POST /admin/train-jamie` → extract + `ModelManager.train_property_manager()` → fine-tunes `peteollama:property-manager`. |
| **Env overrides**   | ✅ `PETE_DB_PATH` lets you point to any SQLite.                                                                              |
| **Startup script**  | ✅ `runpod_start.sh` pulls `qwen3:30b`, installs deps, auto-kills old servers, auto-pulls missing Ollama model.              |

### How it all fits together

```mermaid
graph TD
    A[RunPod pod boot] --> B(runpod_start.sh)
    B --> C[virtual env + deps]
    C --> D[Check/ Pull base model qwen3:30b]
    D --> E[Start Uvicorn src/main.py]
    E --> F[FastAPI: VAPIWebhookServer]
    subgraph User Flows
        F --> G[/ui – chat playground/]
        F --> H[/admin – dashboard/]
        G -->|POST /test/stream| I[ModelManager.generate_stream]
        H -->|GET /admin/training-samples| J[PeteDBManager.get_training_examples]
        H -->|POST /admin/train-jamie| K[virtual_jamie_extractor]
        K --> L[/app/pete.db]
        K --> M[ModelManager.train_property_manager]
        M --> N[peteollama:property-manager tag]
        N --> G
    end
```

### How to run locally

```bash
# clone & enter repo
git clone https://github.com/Mark0025/Pete_ollama_agent.git
cd Pete_ollama_agent

# install uv (if missing) and run
pip install uv
uv venv .venv
source .venv/bin/activate
uv pip install -r requirements.txt

# (optional) export PETE_DB_PATH or set PROD_DB_* vars for extractor
export PETE_DB_PATH=$(pwd)/pete.db

# launch server
uvicorn src.main:app --reload --port 8000
```

Then open:

- `http://localhost:8000/ui` – chat.
- `http://localhost:8000/admin` – training dashboard.

### Next tasks

- [ ] Style admin dashboard, add charts/ counts.
- [ ] Secure admin endpoints (basic auth).
- [ ] Add automated unit tests (pytest).
