# Medical Triage Agent - Architecture Diagram

## System Architecture Overview

```mermaid
graph TB
    subgraph "User Interface"
        UI[Web UI<br/>React + Vite]
        WS[WebSocket<br/>Real-time Communication]
    end

    subgraph "Backend Services"
        API[FastAPI Server<br/>web_ui/app.py]
        ADK[ADK Runner<br/>Agent Orchestration]
    end

    subgraph "Root Agent"
        ROOT[root_agent<br/>Orchestrator]
    end

    subgraph "Sub-Agents"
        INTERVIEW[interview_agent<br/>Symptom Collection]
        REASONING[reasoning_agent<br/>Triage Analysis]
        EXECUTION[execution_agent<br/>Action Planning]
        DOC[documentation_agent<br/>SOAP Documentation]
    end

    subgraph "Tools & Knowledge Base"
        EXTRACT[extract_symptoms<br/>NLP Extraction]
        BATES[query_bates_guide<br/>Physical Exam Guide]
        BPJS[check_bpjs_criteria<br/>Emergency Criteria]
        CHROMA[Chroma Vector DB<br/>Knowledge Base]
    end

    subgraph "State Management"
        STATE[Session State<br/>InMemorySessionService]
        SYMPTOMS[symptoms_data<br/>JSON Symptoms]
        TRIAGE[triage_result<br/>Triage Level]
        EXEC[execution_result<br/>Action Plan]
        SOAP[medical_documentation<br/>SOAP Note]
    end

    subgraph "Cloud Infrastructure"
        CR[Cloud Run<br/>Container Service]
        GCS[Cloud Storage<br/>Chroma Persistence]
        VERTEX[Vertex AI<br/>Gemini Models]
    end

    UI -->|WebSocket| WS
    WS -->|Messages| API
    API -->|Stream Events| ADK
    ADK -->|Delegates| ROOT

    ROOT -->|Delegates| INTERVIEW
    ROOT -->|Delegates| REASONING
    ROOT -->|Delegates| EXECUTION
    ROOT -->|Delegates| DOC

    INTERVIEW -->|Uses| EXTRACT
    INTERVIEW -->|Uses| BATES
    REASONING -->|Uses| BPJS
    REASONING -->|Uses| CHROMA
    EXECUTION -->|Uses| CHROMA

    BATES -->|Queries| CHROMA
    BPJS -->|Queries| CHROMA

    INTERVIEW -->|Saves| SYMPTOMS
    REASONING -->|Reads| SYMPTOMS
    REASONING -->|Saves| TRIAGE
    EXECUTION -->|Reads| TRIAGE
    EXECUTION -->|Saves| EXEC
    DOC -->|Reads| SYMPTOMS
    DOC -->|Reads| TRIAGE
    DOC -->|Reads| EXEC
    DOC -->|Saves| SOAP

    ADK -->|Manages| STATE
    STATE -->|Stores| SYMPTOMS
    STATE -->|Stores| TRIAGE
    STATE -->|Stores| EXEC
    STATE -->|Stores| SOAP

    API -->|Deployed on| CR
    CHROMA -->|Persisted to| GCS
    ADK -->|Uses| VERTEX

    style ROOT fill:#e1f5ff
    style INTERVIEW fill:#c8e6c9
    style REASONING fill:#bbdefb
    style EXECUTION fill:#ffe0b2
    style DOC fill:#e1bee7
    style CHROMA fill:#fff9c4
    style STATE fill:#f3e5f5
```

## Agent Workflow

```mermaid
sequenceDiagram
    participant User
    participant UI
    participant API
    participant Root
    participant Interview
    participant Reasoning
    participant Execution
    participant Doc
    participant Chroma

    User->>UI: Input Symptoms
    UI->>API: WebSocket Message
    API->>Root: Delegate Task

    Root->>Root: Check State
    alt No symptoms_data
        Root->>Interview: Delegate Interview
        Interview->>Chroma: Query Bates Guide
        Chroma-->>Interview: Guide Results
        Interview->>User: Ask Questions
        User->>Interview: Provide Answers
        Interview->>Interview: extract_symptoms()
        Interview->>State: Save symptoms_data
        Interview->>Reasoning: Transfer
    end

    Root->>Reasoning: Delegate Analysis
    Reasoning->>State: Read symptoms_data
    Reasoning->>Chroma: Query BPJS Criteria
    Chroma-->>Reasoning: Criteria Results
    Reasoning->>Reasoning: Analyze & Classify
    Reasoning->>State: Save triage_result

    alt Data Incomplete
        Reasoning->>Interview: Transfer Back
        Interview->>User: Ask Missing Info
        User->>Interview: Provide Info
        Interview->>Interview: Re-extract
        Interview->>State: Update symptoms_data
        Interview->>Reasoning: Transfer Back
    end

    Root->>Execution: Delegate Action
    Execution->>State: Read triage_result
    Execution->>Chroma: Query Guidelines
    Execution->>Execution: Plan Actions
    Execution->>State: Save execution_result

    Root->>Doc: Delegate Documentation
    Doc->>State: Read All Data
    Doc->>Doc: Generate SOAP
    Doc->>State: Save medical_documentation

    Doc->>API: Stream Response
    API->>UI: WebSocket Events
    UI->>User: Display Results
```

## Knowledge Base Architecture

```mermaid
graph LR
    subgraph "Knowledge Sources"
        PDF1[BPJS Criteria PDF<br/>59 chunks]
        PDF2[PPK Kemenkes PDF<br/>2,346 chunks]
        PDF3[Bates Guide PDF<br/>2,504 chunks]
    end

    subgraph "Chroma Vector Database"
        COLL1[bpjs_criteria<br/>Collection]
        COLL2[ppk_kemenkes<br/>Collection]
        COLL3[bates_guide<br/>Collection]
    end

    subgraph "Embedding Model"
        EMBED[text-embedding-004<br/>Vertex AI<br/>768 dimensions]
    end

    subgraph "Query Tools"
        Q1[query_bpjs_criteria]
        Q2[query_ppk_kemenkes]
        Q3[query_bates_guide]
    end

    PDF1 -->|Extract & Chunk| EMBED
    PDF2 -->|Extract & Chunk| EMBED
    PDF3 -->|Extract & Chunk| EMBED

    EMBED -->|Generate Vectors| COLL1
    EMBED -->|Generate Vectors| COLL2
    EMBED -->|Generate Vectors| COLL3

    COLL1 -->|Semantic Search| Q1
    COLL2 -->|Semantic Search| Q2
    COLL3 -->|Semantic Search| Q3

    Q1 -->|Results| REASONING[reasoning_agent]
    Q2 -->|Results| REASONING
    Q3 -->|Results| INTERVIEW[interview_agent]
    Q3 -->|Results| EXECUTION[execution_agent]
```

## State Management Flow

```mermaid
stateDiagram-v2
    [*] --> Empty: Session Start

    Empty --> Interviewing: User Input
    Interviewing --> SymptomsExtracted: extract_symptoms()

    SymptomsExtracted --> Analyzing: Transfer to reasoning_agent
    Analyzing --> TriageComplete: check_bpjs_criteria()

    TriageComplete --> Planning: Transfer to execution_agent
    Planning --> ActionComplete: Generate Action Plan

    ActionComplete --> Documenting: Transfer to documentation_agent
    Documenting --> Complete: Generate SOAP Note

    Analyzing --> Interviewing: Data Incomplete<br/>Transfer Back

    Complete --> [*]

    note right of SymptomsExtracted
        symptoms_data:
        - gejala_utama
        - gejala_penyerta
        - durasi
        - tingkat_keparahan
        - riwayat_medis
        - obat
    end note

    note right of TriageComplete
        triage_result:
        - triage_level (1-5)
        - kriteria_terpenuhi
        - alasan
        - rekomendasi
    end note

    note right of ActionComplete
        execution_result:
        - tindakan
        - fasilitas
        - prioritas
        - estimasi_waktu
    end note

    note right of Complete
        medical_documentation:
        - SOAP Note
        - Complete Medical Record
    end note
```

## Deployment Architecture

```mermaid
graph TB
    subgraph "Development"
        DEV[Local Development<br/>Python + React]
    end

    subgraph "Build Process"
        BUILD[Cloud Build<br/>Docker Image]
        FRONTEND[Frontend Build<br/>Vite + React]
        DOCKER[Dockerfile<br/>Multi-stage Build]
    end

    subgraph "Cloud Run"
        CR[Cloud Run Service<br/>medical-triage-agent]
        CONTAINER[Container<br/>FastAPI + ADK]
    end

    subgraph "Storage"
        GCS[Cloud Storage<br/>chroma-db bucket]
        CHROMA_LOCAL[Local Chroma DB<br/>/app/chroma_db]
    end

    subgraph "AI Services"
        VERTEX[Vertex AI<br/>Gemini Models]
        EMBED[Embedding API<br/>text-embedding-004]
    end

    DEV -->|Deploy| BUILD
    FRONTEND -->|Static Files| DOCKER
    DOCKER -->|Image| BUILD
    BUILD -->|Push| CR

    CR -->|Runs| CONTAINER
    CONTAINER -->|Startup| CHROMA_LOCAL
    CONTAINER -->|Download| GCS
    CONTAINER -->|Upload| GCS

    CONTAINER -->|API Calls| VERTEX
    CONTAINER -->|Embeddings| EMBED

    CHROMA_LOCAL -.->|Sync| GCS

    style CR fill:#4285f4,color:#fff
    style GCS fill:#34a853,color:#fff
    style VERTEX fill:#ea4335,color:#fff
```

## Agent Communication Pattern

```mermaid
graph TD
    subgraph "LLM-Driven Delegation"
        ROOT[root_agent<br/>Reads State<br/>Decides Next Agent]
    end

    subgraph "State-Based Routing"
        CHECK{Check State}
        CHECK -->|symptoms_data?| REASONING
        CHECK -->|triage_result?| EXECUTION
        CHECK -->|execution_result?| DOC
        CHECK -->|None| INTERVIEW
    end

    subgraph "Agent Responsibilities"
        INTERVIEW[interview_agent<br/>1. Collect Symptoms<br/>2. Query Bates Guide<br/>3. Extract & Save]
        REASONING[reasoning_agent<br/>1. Validate Data<br/>2. Query BPJS/PPK<br/>3. Classify Triage]
        EXECUTION[execution_agent<br/>1. Read Triage<br/>2. Query Guidelines<br/>3. Plan Actions]
        DOC[documentation_agent<br/>1. Read All Data<br/>2. Generate SOAP<br/>3. Save Documentation]
    end

    ROOT -->|Delegates| CHECK
    REASONING -->|Transfer Back| INTERVIEW
    INTERVIEW -->|Transfer| REASONING
    REASONING -->|Transfer| EXECUTION
    EXECUTION -->|Transfer| DOC

    style ROOT fill:#e1f5ff
    style INTERVIEW fill:#c8e6c9
    style REASONING fill:#bbdefb
    style EXECUTION fill:#ffe0b2
    style DOC fill:#e1bee7
```

## Key Components

### 1. **Root Agent (Orchestrator)**

- **Role**: Central coordinator that routes tasks to appropriate sub-agents
- **Decision Logic**: Reads session state and delegates based on workflow stage
- **State Checks**:
  - `symptoms_data` → delegate to `reasoning_agent`
  - `triage_result` → delegate to `execution_agent`
  - `execution_result` → delegate to `documentation_agent`
  - None → delegate to `interview_agent`

### 2. **Interview Agent**

- **Role**: Collects patient symptoms through dynamic conversation
- **Tools**:
  - `extract_symptoms`: NLP extraction to structured JSON
  - `query_bates_guide`: Semantic search for interview guidance
- **Output**: `symptoms_data` (JSON) saved to session state

### 3. **Reasoning Agent**

- **Role**: Analyzes symptoms and determines triage level (1-5)
- **Tools**:
  - `check_bpjs_criteria`: Analyzes against BPJS emergency criteria
  - `query_bpjs_criteria`: Semantic search for relevant criteria
  - `query_ppk_kemenkes`: Semantic search for health guidelines
- **Output**: `triage_result` with classification and justification
- **Validation**: Can transfer back to `interview_agent` if data incomplete

### 4. **Execution Agent**

- **Role**: Plans actions based on triage level
- **Tools**:
  - `query_bpjs_criteria`: For facility recommendations
  - `query_ppk_kemenkes`: For treatment guidelines
- **Output**: `execution_result` with action plan

### 5. **Documentation Agent**

- **Role**: Generates SOAP medical documentation
- **Input**: Reads all previous state (`symptoms_data`, `triage_result`, `execution_result`)
- **Output**: `medical_documentation` (SOAP note)

### 6. **Knowledge Base (Chroma)**

- **Collections**:
  - `bpjs_criteria`: BPJS emergency criteria (59 chunks)
  - `ppk_kemenkes`: Primary health care guidelines (2,346 chunks)
  - `bates_guide`: Physical examination guide (2,504 chunks)
- **Persistence**: Cloud Storage for fast startup
- **Embedding**: Google's `text-embedding-004` (768 dimensions)

### 7. **State Management**

- **Storage**: `InMemorySessionService` (session-scoped)
- **State Keys**:
  - `symptoms_data`: Extracted symptoms (JSON)
  - `triage_result`: Triage classification (JSON)
  - `execution_result`: Action plan (JSON)
  - `medical_documentation`: SOAP note (text)

## Data Flow

1. **User Input** → WebSocket → FastAPI → ADK Runner
2. **Root Agent** → Checks state → Delegates to appropriate agent
3. **Interview Agent** → Queries Bates Guide → Asks questions → Extracts symptoms
4. **Reasoning Agent** → Validates data → Queries BPJS/PPK → Classifies triage
5. **Execution Agent** → Reads triage → Queries guidelines → Plans actions
6. **Documentation Agent** → Reads all data → Generates SOAP → Saves documentation
7. **Response** → ADK Runner → FastAPI → WebSocket → User Interface

## Error Handling & Edge Cases

1. **Incomplete Data**: `reasoning_agent` can transfer back to `interview_agent`
2. **Re-extraction**: `interview_agent` can re-extract after receiving missing info
3. **State Validation**: Each agent validates required state before proceeding
4. **Non-blocking Init**: Chroma initialization runs in background on startup
5. **Cloud Storage Fallback**: If Chroma DB not in GCS, initializes locally then uploads
