# Technical Specifications & Database Comparison

Dokumen ini menjelaskan spesifikasi teknis, perbandingan vector database, dan kompatibilitas dengan berbagai teknologi untuk Medical Triage Agent.

---

## 📊 Vector Database Comparison

### Quick Comparison

| Vector DB | Type | Free Tier | Min Spec (Self-hosted) | Best For |
|-----------|------|-----------|----------------------|----------|
| **Vertex AI Vector Search** | Managed (GCP) | ❌ No free tier | N/A (Managed) | Google Cloud users |
| **Pinecone** | Managed | ✅ Free tier (Starter) | N/A (Managed) | Quick start, production |
| **Qdrant** | Open Source + Cloud | ✅ Free (self-hosted) | 2 CPU, 8GB RAM | Cost-effective, flexible |
| **Chroma** | Open Source | ✅ Free | 2 CPU, 8GB RAM | Simple, lightweight |
| **Weaviate** | Open Source + Cloud | ✅ Free (self-hosted) | 2 CPU, 8GB RAM | GraphQL, advanced features |
| **Milvus** | Open Source + Cloud | ✅ Free (self-hosted) | 4 CPU, 8GB RAM | Large scale, distributed |

---

## 1. Chroma Vector Database

### Overview
- **Type:** Open source, lightweight
- **Best for:** Simple use cases, development, small projects

### Minimum Specifications

#### Untuk Development/Testing
- **CPU:** 2-4 cores (2.0 GHz+)
- **RAM:** 8 GB minimum
- **Storage:** 10-20 GB SSD (untuk OS + Chroma)
- **OS:** 
  - Linux (Ubuntu 20.04+ recommended)
  - macOS 10.14+
  - Windows 10 (2004+) atau Windows 11
- **Python:** 3.8 atau lebih baru
- **Network:** 100 Mbps (untuk local development)

#### Untuk Production (Small-Medium Scale)
- **CPU:** 4-8 cores (2.5 GHz+)
- **RAM:** 16 GB minimum, 32 GB recommended
- **Storage:** 50-100 GB SSD/NVMe
- **OS:** Linux (Ubuntu 22.04 LTS recommended)
- **Network:** 1 Gbps

### Perhitungan RAM

Chroma menyimpan indeks HNSW vektor di dalam memori (RAM) untuk pencarian cepat.

**Formula RAM:**
```
RAM yang dibutuhkan = jumlah_vektor × dimensi_vektor × 4 bytes
```

**Contoh Perhitungan untuk Bates Guide (12MB PDF):**
- Estimated chunks: ~600-1000 chunks
- Embedding dimension: 768 (text-embedding-004) atau 1536 (text-embedding-004-large)

**Dengan 768 dimensi:**
- 1,000 vectors × 768 × 4 bytes = **3 MB RAM** ✅ (sangat kecil!)

**Dengan 1536 dimensi:**
- 1,000 vectors × 1536 × 4 bytes = **6 MB RAM** ✅ (masih sangat kecil!)

**Kesimpulan:** Untuk use case Medical Triage Agent, bahkan 8 GB RAM sudah **lebih dari cukup**!

### Storage Requirements:
- **Vectors:** ~2-12 MB (tergantung dimensi)
- **Metadata:** ~1-2 MB
- **Index files:** ~5-10 MB
- **Total:** ~10-25 MB untuk Bates Guide

### Python Requirements
- **Python 3.8+** (recommended: Python 3.10+)

### Installation
```bash
pip install chromadb
# atau dengan uv
uv pip install chromadb
```

### Deployment Options

#### Option 1: Embedded Mode (Simplest)
**Spesifikasi:** Sesuai minimum spec di atas
```python
import chromadb
client = chromadb.Client()
# Data disimpan di local filesystem
```

#### Option 2: Client-Server Mode (Recommended untuk Production)
**Spesifikasi:** 
- Server: 4 CPU, 16 GB RAM minimum
- Client: Bisa lebih rendah (hanya API calls)

```bash
# Run Chroma server
docker run -p 8000:8000 ghcr.io/chroma-core/chroma:latest

# atau dengan Python
chroma run --path /path/to/data --port 8000
```

#### Option 3: Docker Deployment
```bash
docker run -it --rm \
  --name chroma \
  -p 8000:8000 \
  -v /path/to/data:/chroma/chroma \
  ghcr.io/chroma-core/chroma:latest
```

### Spesifikasi untuk Use Case Medical Triage Agent

**Current Knowledge Base:**
1. **Bates Guide to Physical Examination** (12 MB PDF)
   - Estimated chunks: ~600-1000
   - RAM needed: ~3-6 MB
   - Storage: ~10-25 MB

2. **Pedoman BPJS Kriteria Gawat Darurat** (5.3 MB PDF)
   - Estimated chunks: ~300-500
   - RAM needed: ~1.5-3 MB
   - Storage: ~5-15 MB

3. **PPK Kemenkes** (19 MB PDF)
   - Estimated chunks: ~1000-1500
   - RAM needed: ~5-9 MB
   - Storage: ~20-40 MB

**Total Requirements:**
- **Total Vectors:** ~2,000-3,000 vectors
- **Total RAM:** ~10-20 MB (sangat kecil!)
- **Total Storage:** ~35-80 MB
- **With overhead:** ~100-200 MB total

**Recommended Spec untuk Project Ini:**
- **CPU:** 2 cores (cukup)
- **RAM:** 8 GB (lebih dari cukup, bahkan 4 GB bisa)
- **Storage:** 1 GB (lebih dari cukup)
- **OS:** Linux, macOS, atau Windows

**Kesimpulan:** Bahkan laptop dengan 4 GB RAM bisa menjalankan Chroma untuk use case ini!

---

## 2. Other Vector Database Options

### Vertex AI Vector Search (Google Cloud)

**Overview:**
- **Type:** Fully managed service by Google Cloud
- **Integration:** Native dengan Google Cloud ecosystem
- **Best for:** Projects already on GCP, enterprise scale

**Minimum Specifications:**
- **Managed Service:** No infrastructure to manage
- **Requirements:** Google Cloud Project with billing enabled
- **API Access:** REST API, Python SDK

**Pricing (Approximate):**
- **No free tier** - Pay per use
- **Index Creation:** ~$0.10 per hour per index
- **Query Operations:** ~$0.0001 per query
- **Storage:** ~$0.10 per GB/month

**Pros:**
- ✅ Native integration dengan Google Cloud
- ✅ Fully managed, no infrastructure
- ✅ Scalable untuk enterprise
- ✅ Integrated dengan Vertex AI models

**Cons:**
- ❌ No free tier
- ❌ Vendor lock-in ke Google Cloud
- ❌ More expensive untuk small projects

### Pinecone

**Overview:**
- **Type:** Fully managed cloud service
- **Best for:** Quick start, production-ready, no infrastructure management

**Minimum Specifications:**
- **Managed Service:** No infrastructure to manage
- **Free Tier (Starter):**
  - 1 index
  - 100K vectors
  - 1 dimension (up to 1536)
  - Metadata filtering
  - Basic support

**Pricing:**
- **Starter (Free):** 100K vectors, 1 index
- **Standard:** $70/month - 1M vectors, 5 indexes
- **Enterprise:** Custom pricing

**Pros:**
- ✅ Free tier untuk testing
- ✅ Very easy setup
- ✅ Production-ready
- ✅ Good documentation
- ✅ Fast query performance

**Cons:**
- ❌ Limited free tier
- ❌ Can be expensive at scale
- ❌ Vendor lock-in

### Qdrant

**Overview:**
- **Type:** Open source + Managed cloud option
- **Best for:** Cost-effective, flexible deployment, self-hosting

**Minimum Specifications (Self-hosted):**
- **CPU:** 2 cores (2.0 GHz+)
- **RAM:** 8 GB minimum, 16 GB recommended
- **Storage:** 20 GB SSD minimum
- **OS:** Linux (Ubuntu 22.04 LTS recommended)
- **Network:** 100 Mbps minimum

**Pricing:**
- **Self-hosted:** Free (open source)
- **Qdrant Cloud:**
  - Free tier: 1 cluster, 1GB storage
  - Starter: $25/month
  - Production: Custom pricing

**Pros:**
- ✅ Free self-hosted option
- ✅ Open source
- ✅ Good performance
- ✅ Flexible deployment
- ✅ REST and gRPC APIs

**Cons:**
- ⚠️ Need to manage infrastructure (self-hosted)
- ⚠️ Setup more complex than managed

### Weaviate

**Overview:**
- **Type:** Open source + Managed cloud
- **Best for:** GraphQL API, advanced features, hybrid search

**Minimum Specifications (Self-hosted):**
- **CPU:** 2 cores
- **RAM:** 8 GB minimum, 16 GB recommended
- **Storage:** 20 GB SSD
- **OS:** Linux, macOS, Windows
- **Docker:** Required

**Pricing:**
- **Self-hosted:** Free (open source)
- **Weaviate Cloud:** 
  - Free tier: Limited
  - Paid: Custom pricing

**Pros:**
- ✅ GraphQL API
- ✅ Advanced features (hybrid search, etc.)
- ✅ Good documentation
- ✅ Open source option

**Cons:**
- ⚠️ More complex setup
- ⚠️ Steeper learning curve
- ⚠️ May be overkill for simple use cases

### Milvus

**Overview:**
- **Type:** Open source + Managed cloud
- **Best for:** Large scale, distributed systems, enterprise

**Minimum Specifications (Self-hosted):**
- **CPU:** 4 cores minimum
- **RAM:** 8 GB (standalone), 32 GB (cluster)
- **Storage:** SSD SATA 3.0+
- **OS:** Linux, macOS
- **Docker:** Required

**Pricing:**
- **Self-hosted:** Free (open source)
- **Zilliz Cloud (Managed):** Custom pricing

**Pros:**
- ✅ Highly scalable
- ✅ Distributed architecture
- ✅ Production-ready
- ✅ Good for large datasets

**Cons:**
- ❌ Complex setup
- ❌ Overkill for small projects
- ❌ Higher resource requirements

---

## 🎯 Rekomendasi untuk Medical Triage Agent

### Untuk Development & Testing
**Rekomendasi: Chroma atau Qdrant (self-hosted)**
- ✅ Free
- ✅ Simple setup
- ✅ Cukup untuk testing dengan Bates Guide (12MB PDF)

### Untuk Production (Small-Medium Scale)
**Rekomendasi: Pinecone (Starter) atau Qdrant Cloud**
- ✅ Managed service (less maintenance)
- ✅ Good performance
- ✅ Reasonable pricing

### Untuk Production (Large Scale)
**Rekomendasi: Vertex AI Vector Search atau Milvus**
- ✅ Scalable
- ✅ Enterprise-ready
- ✅ Better untuk banyak dokumen

**My Top Pick:** Start with **Chroma** for development, migrate to **Pinecone** or **Qdrant Cloud** for production if needed.

---

## 🔧 LangChain & LangSmith Compatibility dengan Google ADK

### Quick Answer

**Apakah kompatibel?**
- ✅ **LangChain Tools:** Ya, ADK memiliki `LangchainTool` wrapper
- ✅ **Chroma dengan LangChain:** Ya, tapi ada isu kompatibilitas versi
- ⚠️ **LangSmith Monitoring:** Bisa, tapi tidak native untuk ADK
- ❓ **Apakah perlu?** **TIDAK** untuk use case ini - ADK sudah cukup powerful

### LangChain Integration dengan ADK

#### 1. LangChain Tools dengan ADK

ADK memiliki built-in support untuk LangChain tools melalui `LangchainTool` wrapper.

**Cara Menggunakan:**
```python
from google.adk.tools import LangchainTool
from langchain.tools import Tool

# Define LangChain tool
langchain_tool = Tool(
    name="search",
    func=search_function,
    description="Search the web"
)

# Wrap dengan ADK
adk_tool = LangchainTool(langchain_tool)

# Use in agent
from google.adk.agents import Agent

agent = Agent(
    model="gemini-2.5-flash",
    tools=[adk_tool],
    # ... other config
)
```

#### 2. LangChain Vector Stores dengan ADK

**Chroma + LangChain:**
- ✅ LangChain memiliki `Chroma` vector store integration
- ⚠️ Ada isu kompatibilitas dengan versi Chroma terbaru (Rust-based)
- ✅ Bisa digunakan, tapi perlu perhatian versi

**Setup:**
```python
from langchain.vectorstores import Chroma
from langchain.embeddings import GoogleGenerativeAIEmbeddings

# Initialize embeddings
embeddings = GoogleGenerativeAIEmbeddings(
    model="models/text-embedding-004"
)

# Create Chroma vector store
vectorstore = Chroma(
    collection_name="bates_guide",
    embedding_function=embeddings,
    persist_directory="./chroma_db"
)

# Use in LangChain chain
from langchain.chains import RetrievalQA

qa_chain = RetrievalQA.from_chain_type(
    llm=your_llm,
    retriever=vectorstore.as_retriever()
)
```

#### 3. LangChain dengan ADK Tools

Anda bisa membuat ADK tool yang menggunakan LangChain:

```python
from google.adk.tools import FunctionTool
from langchain.vectorstores import Chroma

def query_knowledge_base(question: str) -> str:
    """Query knowledge base using LangChain + Chroma"""
    # Use LangChain to query Chroma
    results = vectorstore.similarity_search(question, k=3)
    return "\n".join([doc.page_content for doc in results])

# Create ADK tool
knowledge_tool = FunctionTool(func=query_knowledge_base)

# Use in ADK agent
agent = Agent(
    model="gemini-2.5-flash",
    tools=[knowledge_tool],
)
```

### LangSmith Monitoring

#### Apakah LangSmith Bisa Digunakan dengan ADK?

**Jawaban Singkat:** Bisa, tapi **tidak native**. ADK tidak secara otomatis mengirim traces ke LangSmith.

#### Cara Mengintegrasikan LangSmith:

**Option 1: Manual Tracing (Recommended)**
```python
from langsmith import traceable
from google.adk.runners import InMemoryRunner

@traceable(name="medical_triage_agent")
async def run_agent_with_tracing(user_input: str):
    runner = InMemoryRunner(agent=root_agent)
    # ... run agent
    result = await runner.run_async(...)
    return result
```

**Option 2: Custom Callback**
```python
from langsmith import Client
from google.adk.agents import BaseAgent

class LangSmithCallback:
    def __init__(self):
        self.client = Client()
    
    def on_agent_start(self, agent_name: str, input_data: dict):
        # Log to LangSmith
        pass
    
    def on_agent_end(self, agent_name: str, output_data: dict):
        # Log to LangSmith
        pass
```

**Setup LangSmith:**
```bash
# Install
pip install langsmith

# Set environment variables
export LANGSMITH_API_KEY="your-api-key"
export LANGSMITH_PROJECT="medical-triage-agent"
export LANGSMITH_TRACING="true"
```

### Apakah Perlu LangChain untuk Project Ini?

**Current Setup:**
- ✅ Google ADK untuk agent orchestration
- ✅ Google Gemini untuk LLM
- ✅ Custom tools dengan FunctionTool
- ✅ Direct PDF access untuk knowledge base

**Jika Menambahkan LangChain:**
- ✅ Bisa menggunakan LangChain vector stores (Chroma)
- ✅ Bisa menggunakan LangChain chains
- ⚠️ Menambah complexity
- ⚠️ Dependency tambahan
- ⚠️ Tidak ada benefit signifikan untuk use case ini

**Rekomendasi:**

**TIDAK PERLU LangChain** untuk project ini karena:

1. **ADK sudah powerful:** ADK sudah memiliki semua yang dibutuhkan
2. **Direct PDF access lebih baik:** Langsung akses PDF lebih efisien daripada vector DB untuk dokumen kecil
3. **Less dependencies:** Semakin sedikit dependency, semakin mudah maintenance
4. **Google ecosystem:** ADK + Gemini sudah terintegrasi dengan baik

**Kapan Perlu LangChain:**
- Jika perlu banyak LangChain integrations (100+ tools)
- Jika team sudah familiar dengan LangChain
- Jika perlu migrate dari LangChain ke ADK

### Rekomendasi untuk Medical Triage Agent

#### Option 1: Pure ADK (Current - Recommended) ✅

**Keuntungan:**
- ✅ Simple, no extra dependencies
- ✅ Native Google Cloud integration
- ✅ Direct PDF access (lebih efisien untuk dokumen kecil)
- ✅ Less complexity

**Implementasi:**
```python
# Current approach - direct PDF access
from google.genai import types

pdf_content = types.Part.from_bytes(
    data=pdf_bytes,
    mime_type="application/pdf"
)
# Use directly with Gemini
```

#### Option 2: ADK + Chroma (Without LangChain) ✅

**Keuntungan:**
- ✅ Vector search untuk semantic search
- ✅ Scalable untuk banyak dokumen
- ✅ Tidak perlu LangChain (direct Chroma API)

**Implementasi:**
```python
import chromadb
from google.adk.tools import FunctionTool

# Direct Chroma (no LangChain)
client = chromadb.Client()
collection = client.get_collection("bates_guide")

def query_chroma(question: str) -> str:
    results = collection.query(
        query_texts=[question],
        n_results=3
    )
    return "\n".join(results['documents'][0])

tool = FunctionTool(func=query_chroma)
```

#### Option 3: ADK + LangChain + Chroma (Not Recommended) ❌

**Kekurangan:**
- ❌ Extra dependency (LangChain)
- ❌ Version compatibility issues
- ❌ More complexity
- ❌ No significant benefit

### Comparison Table

| Feature | Pure ADK | ADK + Chroma | ADK + LangChain + Chroma |
|---------|----------|--------------|--------------------------|
| **Complexity** | ⭐ Low | ⭐⭐ Medium | ⭐⭐⭐ High |
| **Dependencies** | Minimal | + Chroma | + LangChain + Chroma |
| **Performance** | ⭐⭐⭐ Fast | ⭐⭐⭐ Fast | ⭐⭐ Medium |
| **Scalability** | ⭐⭐ Medium | ⭐⭐⭐ High | ⭐⭐⭐ High |
| **Maintenance** | ⭐⭐⭐ Easy | ⭐⭐ Medium | ⭐ Hard |
| **Best For** | Small docs | Many docs | LangChain ecosystem |

### LangSmith untuk Monitoring

#### Apakah Perlu LangSmith?

**Untuk Development:** ✅ Bisa berguna untuk debugging
**Untuk Production:** ⚠️ Optional, ADK sudah punya logging

#### Alternatif Monitoring:

1. **Google Cloud Logging** (Recommended untuk GCP)
   ```python
   import logging
   from google.cloud import logging as cloud_logging
   
   client = cloud_logging.Client()
   client.setup_logging()
   ```

2. **ADK Built-in Logging**
   ```python
   import logging
   logging.basicConfig(level=logging.INFO)
   # ADK automatically logs agent execution
   ```

3. **Custom Monitoring**
   ```python
   # Track agent calls manually
   def track_agent_call(agent_name, input, output):
       # Send to your monitoring system
       pass
   ```

### Final Recommendation

**Untuk Medical Triage Agent:**

**Recommended Approach:**
1. **Development:** Pure ADK dengan direct PDF access (current)
2. **Jika perlu vector search:** ADK + Chroma (direct, tanpa LangChain)
3. **Monitoring:** Google Cloud Logging (native untuk GCP)

**TIDAK PERLU:**
- ❌ LangChain (tidak ada benefit signifikan)
- ❌ LangSmith (optional, bisa pakai Cloud Logging)

### Migration Path (Jika Perlu Vector DB):

```python
# Step 1: Install Chroma
pip install chromadb

# Step 2: Create tool (no LangChain needed)
from google.adk.tools import FunctionTool
import chromadb

def query_knowledge_base(question: str) -> str:
    client = chromadb.Client()
    collection = client.get_collection("bates_guide")
    results = collection.query(
        query_texts=[question],
        n_results=3
    )
    return "\n".join(results['documents'][0])

# Step 3: Use in agent
tool = FunctionTool(func=query_knowledge_base)
agent = Agent(model="gemini-2.5-flash", tools=[tool])
```

---

## 📚 Resources

- [Chroma Documentation](https://docs.trychroma.com/)
- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [Pinecone Documentation](https://docs.pinecone.io/)
- [Vertex AI Vector Search](https://cloud.google.com/vertex-ai/docs/vector-search/overview)
- [Weaviate Documentation](https://weaviate.io/developers/weaviate)
- [Milvus Documentation](https://milvus.io/docs)
- [ADK LangchainTool Documentation](https://github.com/google/adk-python)
- [LangChain Chroma Integration](https://docs.langchain.com/integrations/vectorstores/chroma)
- [LangSmith Documentation](https://docs.smith.langchain.com/)

---

## ✅ Checklist

- [ ] **Current setup sudah cukup?** ✅ Ya, untuk dokumen kecil
- [ ] **Perlu LangChain?** ❌ Tidak perlu
- [ ] **Perlu LangSmith?** ⚠️ Optional, bisa pakai Cloud Logging
- [ ] **Perlu Vector DB?** ⚠️ Optional, hanya jika banyak dokumen
- [ ] **Jika perlu Vector DB:** ✅ Pakai Chroma langsung (tanpa LangChain)

---

*Last Updated: November 2025*

