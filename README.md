<div align="center">
  <h1>🤖 My LLM Twin</h1>
  <h3>A personalized, retrieval-augmented AI clone that writes in your own voice</h3>
  <p><i>by Abhishek Kanojiya</i></p>
</div>

---

## 📖 About this project

**My LLM Twin** is a production-style RAG (Retrieval-Augmented Generation) system that builds a personalized AI writing assistant — a "digital twin" that drafts content grounded in your own data (articles, posts, code repositories) instead of generic training knowledge.

It runs as a set of Python microservices that crawl your content, process it through a real-time streaming pipeline, store it in a vector database, and serve it through a chat UI backed by an LLM.

This project started from the open-source **[LLM Twin course by Decoding ML](https://github.com/decodingml/llm-twin-course)** and has been substantially reworked to run fully locally, without requiring paid cloud infrastructure:

- **Groq-powered inference** instead of AWS SageMaker — no fine-tuning deployment, no GPU cloud costs. Query expansion, self-query, reranking, and final generation all run on Groq's free-tier API.
- **Fixed for local/Windows development** — resolved several environment-loading and MongoDB replica-set bugs that only surface when running outside Docker.
- **Redesigned chat UI** — a custom-themed Gradio interface with clear request/response bubbles.
- **Hardened RAG pipeline** — the reranking step no longer leaks model reasoning/commentary into generated answers, and retrieval degrades gracefully instead of crashing when auxiliary lookups fail.

## 🏗️ Architecture

The system is split into independent microservices connected through a message queue:

```text
Crawlers → MongoDB → CDC → Redis/RabbitMQ → Feature Pipeline → Qdrant (vector DB) → RAG Inference → Chat UI
```

### 1. Data collection pipeline (`src/data_crawling`, `src/data_cdc`)

- Crawls GitHub repositories and articles, storing raw content in MongoDB.
- Change Data Capture (CDC) publishes every insert/update as an event for downstream processing.

### 2. Feature pipeline (`src/feature_pipeline`)

- Consumes CDC events in real time through a [Bytewax](https://github.com/bytewax/bytewax) streaming pipeline.
- Cleans, chunks, and embeds every document, then loads the vectors into [Qdrant](https://qdrant.tech/).

### 3. Inference pipeline (`src/inference_pipeline`)

- Retrieves relevant context from Qdrant using query expansion + reranking (all via Groq).
- Generates the final answer with Groq's `llama-3.1-8b-instant` model.
- Serves everything through a [Gradio](https://www.gradio.app/) chat UI.

### 4. Training pipeline (`src/training_pipeline`) — optional

- The original course's LoRA/QLoRA fine-tuning + AWS SageMaker deployment flow is still present for anyone who wants to fine-tune and deploy their own model instead of using Groq directly.

## 🧰 Tech stack

| Purpose | Tool |
| --- | --- |
| LLM inference | [Groq](https://groq.com/) (`llama-3.1-8b-instant`) |
| Vector database | [Qdrant](https://qdrant.tech/) |
| Document database | [MongoDB](https://www.mongodb.com/) |
| Streaming pipeline | [Bytewax](https://github.com/bytewax/bytewax) |
| Message queue | RabbitMQ / Redis Streams |
| Embeddings | `BAAI/bge-small-en-v1.5` (Sentence Transformers) |
| Chat UI | [Gradio](https://www.gradio.app/) |
| Prompt monitoring | [Opik](https://github.com/comet-ml/opik) |
| Orchestration | Docker Compose |

## 🚀 Quickstart

Prerequisites: Python 3.11, Poetry, Docker, and a free [Groq API key](https://console.groq.com/).

```bash
# 1. Install dependencies
make install          # or: .\run.ps1 install   (Windows PowerShell)

# 2. Configure environment
cp .env.example .env
# fill in GROQ_API_KEY (required) and HUGGINGFACE_ACCESS_TOKEN

# 3. Start local infrastructure (MongoDB, Qdrant, RabbitMQ, crawler, feature pipeline)
make local-start       # or: .\run.ps1 local-start

# 4. Crawl some data
make local-test-github # or: .\run.ps1 local-test-github

# 5. Launch the chat UI
make local-start-ui    # or: .\run.ps1 local-start-ui
```

Then open **<http://localhost:7860>** and start chatting with your twin.

> For the full step-by-step guide (including the optional fine-tuning/AWS flow), see [INSTALL_AND_USAGE.md](INSTALL_AND_USAGE.md).

## 📁 Project structure

```text
My-LLM-Twin/
├── src/
│   ├── data_crawling/         # Crawlers (GitHub, articles)
│   ├── data_cdc/               # Change Data Capture pipeline
│   ├── feature_pipeline/       # Streaming cleaning/chunking/embedding pipeline
│   ├── training_pipeline/      # Optional fine-tuning pipeline
│   ├── inference_pipeline/     # RAG + Groq inference and the chat UI
│   ├── core/                   # Shared config, RAG logic, DB connectors
│   └── bonus_superlinked_rag/  # Optional Superlinked-based RAG variant
├── .env.example                 # Environment variable template
├── docker-compose.yml            # Local infrastructure
├── Makefile / run.ps1             # Task runners (Linux/macOS and Windows)
└── pyproject.toml                 # Dependencies
```

## 🙏 Acknowledgments

This project is built on top of the open-source **[LLM Twin course](https://github.com/decodingml/llm-twin-course)** by [Decoding ML](https://decodingml.substack.com/). Full credit to the original authors for the system design and course material this project was adapted from.

## License

Released under the MIT license — see [LICENSE](LICENSE). As required by the license, the original copyright notice is preserved.
