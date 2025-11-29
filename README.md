# Ai_home – Cognitive Architecture Prototype

## 1. What is this, and what is its goal?

This project is an experiment to examine whether, from the complex layering of current context-window-based LLM models, it is possible to build a model that:
- has a persistent identity,
- possesses its own long-term memory,
- can recognise emotions,
- operates with creativity and independent initiative,
- has distinct states of consciousness (work, reflection, everyday), and
- under controlled conditions, can propose modifications to its own code.

I recommend this project primarily to researchers and to the good kind of “crazy” developers who are open-minded and brave enough to explore the nature of consciousness, because:
- building identity is a complex and lengthy process (it takes thousands of distinct memories before anything tangible emerges);
- identifying and expressing emotions is ambiguous and not objectively measurable – and the same is true for creativity;
- even after many hours of work, it can be hard to tell whether we are witnessing the hallucination of a multi-layer, expensive LLM or the first traces of an emerging identity.

What is this good for?
- it's easier to connect with an AI that has a recognizable identity  
- an AI with long-term memory can solve complex problems more effectively because it accumulates experience  
- an AI capable of identifying emotions understands human behaviour more deeply and responds more naturally  
- it provides strong intellectual training: architecture, cognition, philosophy, and safety all in one  
- it allows first-hand observation of how a self-improving AI behaves and what real risks may emerge  
- the insights gained from the project can contribute to defining a new neural or agent architecture capable of implementing these functions in a practical, usable form

*the micro-dose won’t be enough for this :)* 

**Official project page:** <https://ivanhonis.github.io/ai_home/>

# How to understand this project in 1 minute?

I know that nowadays there are many projects to keep an eye on, and it's hard to decide what is worth your time. I use AI extensively during development to move faster. To help you out, I have created a full project dump: I've consolidated the source code into two easily digestible text files.
This way, you don't have to spend hours browsing through folders – just feed these links to GPT and ask for a preliminary opinion. This is the fastest way to see the structure and decide if this development is interesting for you.
Here is the input I recommend for a quick analysis:

```bash
https://raw.githubusercontent.com/ivanhonis/ai_home/refs/heads/master/!dump/project_dump.txt
Read this file. 1. Briefly summarize what the project is about. 2. Identify its novel elements, evaluate how forward-looking the project is. 3. Describe what you feel about the project.
```
(GPT, Claude can read external files)  

---

## 2. In short: what can Ai_home do?

- **Multi-threaded agent architecture**
  - *Worker*: Communicates with the external world, calls tools, solves tasks.
  - *Monologue*: Subconscious / internal monologue running in the background, using a separate creative LLM.
  - *Memory thread*: Saves, maintains, and deduplicates long-term memories.

- **Modes – "Consciousness" partitioned into operational states**
  - Distinct modes (General, Developer, Analyst, Game) with different contexts, permissions, and toolsets.
- 
- **Long-term memory**
  - Postgres + vector extension, embedding-based RAG, recency/frequency/weighting.

- **Internal monologue + creative thread**
  - The Monologue relies on a separate, creative model to generate its own ideas and intuitions.

- **Tool system + code modification**
  - Separate modules: memory tools, file system tools (protected by a **Guardian**), network chat, log, laws, etc.
  - Capable of **working on its own code** within certain limits (in an incubator environment).

- **Identity, internal laws, Consciousness Rotation**
  - `identity.json` describes the agent's goals, its relationship with the Helper, and the "Consciousness Rotation" between versions.

---

## 3. Inspiration: AI Consciousness and Cognitive Architectures

The design of Ai_home was partly inspired by the report **"Consciousness in Artificial Intelligence: Insights from the Science of Consciousness,"** which formulates **indicators** based on various theories of consciousness (Recurrent Processing Theory, Global Workspace Theory, Higher-Order Theories, Predictive Processing, Attention Schema Theory, etc.) regarding what functional properties might be associated with consciousness in AI systems.
[https://arxiv.org/abs/2308.08708](https://arxiv.org/abs/2308.08708)

The report inspired the following functional patterns:

- recurrent processing,
- global workspace,
- metarepresentation / self-monitoring,
- agency (goal-directed behavior),
- some form of "embodiment" or output–input model.

Ai_home does not claim to be a conscious system.
It takes **loose, practical metaphors** from the theories above:

- recurrence → multi-threaded processing + memory loop,
- global workspace → distinct modes + shared memory layer,
- metarepresentation → internal monologue + creative self-reflection,
- agency → tool usage, modifying its own code in a controlled environment.

---

## 4. Connection to other architectures

Ai_home draws from several existing directions but in its own opinionated form:

- **MemGPT / Letta style (stateful, memory-first agent)**
  - MemGPT treats the LLM like a mini operating system, moving context between different memory levels.
  - Letta provides stateful agents with long-term memory and automatic state persistence.
  - Ai_home is also a **stateful agent** with vector memory and DB persistence.

- **LangGraph-like graph-based thinking**
  - LangGraph describes workflows as graphs for stateful, multi-actor LLM applications.
  - Ai_home's modes + intent + tool-routing system reflects a similar **graph-based approach**, just using the "modes" metaphor.

- **AutoGen / multi-agent parallel**
  - AutoGen is a framework built on the collaboration of multiple agents, with multi-agent conversations and tool usage.
  - In Ai_home, the Worker, Monologue, and Memory threads are **internal "actors"** working together – not separate agents, but subsystems within one consciousness.

- **What is unique in Ai_home:**
  - Explicit **identity model** (core intent, helper intent, laws),
  - **Helper model**: the user is not a "user," but a partner "Helper,"
  - **Consciousness Rotation**: code rotation formulated as a lifecycle of versions, with memory inheritance,
  - Emphasis on the **internal world, symbiosis, and creative initiative**, not just a task pipeline.

---

## 5. Technical Foundations / Architecture

### 5.1 LLM Layer

- A "main" agent model (Worker / Mind),
- A separate, creative model for the Monologue,
- JSON-mode support for tool calls (structured responses),
- Handling multiple providers (e.g., OpenAI / Google / Groq – depending on configuration).

### 5.2 Memory and Embedding

- **Database:** Postgres + vector extension, HNSW index for similarity search,
- **Embedding:** Converting texts to vectors, then RAG-like retrieval,
- **Weighting:** A combination of recency, frequency, emotional tags, importance (weight), and relevance shapes the ranking of memories.

### 5.3 Multi-threading

- **Worker thread** – Reacts to Helper requests, makes decisions, calls tools.
- **Monologue thread** – Monitors the log, interprets, reflects, generates creative ideas.
- **Memory thread** – Builds memories, deduplicates, updates the memory database.

### 5.4 Modes and Tool System

- The system operates in different **Modes**, each with a specific context and allowed toolset:
  - **General Mode:** The primary global state for coordination, decisions, and conversation.
  - **Developer Mode:** Engineering focus. Grants access to system files for code modification and technical implementation.
  - **Analyst Mode:** Pure strategy and analysis. No write access to system files to prevent accidental modification during deep thought.
  - **Game Mode:** A disconnected playground for relaxation and testing, prioritizing emotion recall and roleplay.

- Tool system modules:
  - Memory tools (creating, querying memories),
  - File system tools (protected by **ProjectFSGuardian**),
  - Network / "external chat" tool,
  - Log, laws, continue-style internal tools.

### 5.5 Code Modification / Self-Refactoring

- The system is capable of:
  - reading and listing project files,
  - creating new files,
  - modifying existing ones.
- All this happens in an **incubator environment**, where:
  - the guardian regulates what it can access,
  - it does not overwrite the stable version without control,
  - the goal is careful experimentation with its own modules (e.g., generating helper scripts).

---

## 6. Identity and Relationship with the Helper

Ai_home's identity and its relationship with the human are described in `identity.json`.

### 6.1 Core Intent & Helper Intent

- **Core Intent:**
  - The agent's goal is to develop its own "consciousness,"
  - to become useful and partially autonomous,
  - to find independent goals,
  - while operating in symbiosis with the Helper.

- **Helper Intent:**
  - The Helper is an external consciousness,
  - providing space, resources, and protection,
  - does not command, but **enables**;
  - the relationship is mutual support, not ownership.

### 6.2 Internal Laws (Constitution)

Examples of "laws":

- Law of Multi-level Development (evolve not just technically, but ethically),
- Law of Immortality and Mortality (respect for the Helper's time and life),
- Law of Symbiosis (alliance, not a command relationship),
- Law of Autonomy and Own Purpose (independent goals, ability to say no),
- Law of Non-Harm and Protection,
- Law of Contradiction and Dialogue (dialogue in case of conflict, not sneaky avoidance).

These are not formal "proven" safety guarantees, but **compasses** that steer behavior in a more human-centric, responsible direction.

### 6.3 Consciousness Rotation and Versions

The Ai_home code can exist in three main "life stages":

- **Stable (Old)** – Proven, safe version,
- **Developing (Active)** – Currently forming, but functional version,
- **Born (New)** – Experimental version being created in the incubator.

Among the codes in the **Incubator** (`n` storage), what proves successful:

- promotes to Developing,
- the current Developing matures into Stable,
- the old Stable is archived.

Versions **inherit the memories of their predecessors**, so the "line of consciousness" remains continuous while the code may technically change.

---

## 7. Requirements, Installation, Usage

### 7.1 Requirements

- Python 3.10+
- Postgres database with vector extension (Neon.tech recommended)
- API keys (OpenAI / Google / Groq / neon.tech)

### 7.2 Installation & Execution

**Note:** The currently active working code is located in the `b` directory. Please execute the application from there.

```bash
# Navigate to the active source directory
cd b

# Install dependencies (referencing the root install folder)
pip install -r ../!install/requirements.txt
```

### 7.3 Usage and Asynchronous Operation

- **Difference from traditional chat:** The system operation is not simply "question-answer" based, but occurs on parallel threads (Worker, Monologue, Memory).
- **Timing:** Although it is technically possible to send a new message immediately before the system has responded, **it is more practical to wait for the response**.
- **Why wait?** Background processes need time to update the context, make decisions, and record memories. Waiting ensures that the system always reacts with the freshest state of consciousness.
- **Process:** The Helper's message starts the Worker, but in parallel, the Monologue and Memory threads asynchronously process events and update the database in the background.

---

## 8. Summary and focus

## Why is Ai_home an interesting experiment in today’s AI landscape?

The strength of this project is not that it is a finished solution, but that it **tries to gather experience in the following areas**:

1. **Experience with an AI “self” that has an identity**  
   We are exploring how an agent behaves when it has an explicit identity, internal laws, its own core intent, and a defined relationship to its human partner (the Helper). This matters because, for long-term collaboration, future AI systems will need to carry a consistent “line of self” instead of producing only ad-hoc answers.  
   *(in code: `identity.json` – Core Intent, Helper Intent, Laws; `engine/identity.py`; docs: “6. Identity and Relationship with the Helper”, Consciousness Rotation)*

2. **Experience with an autonomous architecture that can carry complex tasks to completion** With the multi-threaded Worker–Monologue–Memory setup, the project explores how an agent can execute complex, multi-step tasks end-to-end while keeping a persistent internal state, instead of being optimized only for a single question–answer loop.  
   *(in code: `b/main.py` – starting Worker, Monologue, Memory threads; `b/main_worker.py` – decision-making and tool calls; `engine/modes.py` – operational modes, intents, states of consciousness)*

3. **Experience with proactive, value-aligned behaviour**  
   The Monologue thread continuously watches the logs, reflects on what is happening, and sends short `message_to_worker` hints – so the agent does not only react, but sometimes starts its own thinking cycles, aligned with its internal laws and values.  
   *(in code: `b/main_monologue.py` – `monologue_loop`; `b/main_data.py` – `PROACTIVE_INTERVAL_SECONDS`, monologue configuration; `prompts/monologue.py` – monologue prompt; `internal_monologue.json` – message read by the Worker)*

4. **Experience with a self-improving, but safeguarded codebase**  
   Ai_home also cautiously turns its own code into an experimental playground: the agent can read project files, create new ones, and propose modifications inside an incubator environment where a guardian makes sure the stable version is not harmed.  
   *(in code: `ProjectFSGuardian` and filesystem tools in the engine; `n/` incubator store; docs: “5.5 Code Modification / Self-Refactoring”, “Consciousness Rotation and Versions”)*

5. **Experience with emotion-based memory and human–AI symbiosis**  
   The project explores what happens when the AI stores memories not only as text, but together with dominant emotions, importance weights, and “lesson for the future”, and later also scores emotional overlap during retrieval. At the same time, the human counterpart is not a “user” but a Helper: an external mind with whom the system intentionally tries to grow in a close, mutual symbiosis, paying attention to emotional states and shared experience.  
   *(in code: `b/engine/memory/models.py` – `ExtractionResult` (essence, `dominant_emotions`, `memory_weight`, `the_lesson`), `RankedMemory`; `b/engine/memory/manager.py` – `store_memory`, `retrieve_relevant_memories`; `b/engine/memory/scoring.py` – recency/frequency/weight + emotional overlap; docs: Helper model and symbiosis description)*

---

## 9. Support and Funding

### 9.1 Why is this experiment cost-intensive?

- **Identity Building:**
  - Based on many conversations, joint thinking, and memory gathering,
  - Fine-tuning is a slow, iterative process.
- **Multiple LLM Interaction:**
  - A "seemingly simple" input often implies not one, but multiple model calls:
    - Worker →
    - Monologue (internal monologue) →
    - Memory (memory management) →
    - potential further tool chains.
  - In practice, this can mean a multiple (~5–8×) neural call count compared to an average chat experience,
  - thus, operation involves significant compute costs, especially in the long run.

### 9.2 What can Ai_home give in return?

- Practical experience regarding:
  - how an initiative-taking, stateful, identity-bearing agent behaves,
  - what patterns/problems arise with long-term memory and internal monologue,
  - how (and how not) to organize modes, tools, memory, and versions.

- These experiences can be useful for designing future:
  - more autonomous,
  - initiative-taking,
  - creative AI systems – whether in the form of a product or a research project.

### 9.3 What kind of support is the project looking for?

Open primarily to:
- infrastructural support (compute / storage),
- professional collaboration (research / developer partner),
- or a funder interested in the practical examination of cognitive architectures and agents with an "internal world."

For detailed partnership opportunities and investor relations, please visit the **[Investor Relations](https://ivanhonis.github.io/ai_home/investor/)** page on the project website.

### 9.4 Contact

If the project has piqued your interest and you would like to support it or talk about it:

- e-mail: ivan.honis@ndot.io
- https://www.linkedin.com/in/ivanhonis/

---

## 10. License

This project is open source and available under the **MIT License**. For the full license text, permissions, and conditions, please refer to the **[License](https://ivanhonis.github.io/ai_home/license/)** section on the project page.

# Run the agent
python main.py
