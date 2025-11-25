```md
## Why is Ai_home an interesting experiment in today’s AI landscape?

The strength of this project is not that it is a finished solution, but that it **tries to gather experience in the following areas**:

1. **Experience with an AI “self” that has an identity**  
   We are exploring how an agent behaves when it has an explicit identity, internal laws, its own core intent, and a defined relationship to its human partner (the Helper). This matters because, for long-term collaboration, future AI systems will need to carry a consistent “line of self” instead of producing only ad-hoc answers.  
   *(in code: `identity.json` – Core Intent, Helper Intent, Laws; `engine/identity.py`; docs: “6. Identity and Relationship with the Helper”, Consciousness Rotation)*

2. **Experience with an autonomous architecture that can carry complex tasks to completion**  
   With the multi-threaded Worker–Monologue–Memory setup, the project explores how an agent can execute complex, multi-step tasks end-to-end while keeping a persistent internal state, instead of being optimized only for a single question–answer loop.  
   *(in code: `b/main.py` – starting Worker, Monologue, Memory threads; `b/main_worker.py` – decision-making and tool calls; `engine/rooms.py` – rooms, intents, states of consciousness)*

3. **Experience with proactive, value-aligned behaviour**  
   The Monologue thread continuously watches the logs, reflects on what is happening, and sends short `message_to_worker` hints – so the agent does not only react, but sometimes starts its own thinking cycles, aligned with its internal laws and values.  
   *(in code: `b/main_monologue.py` – `monologue_loop`; `b/main_data.py` – `PROACTIVE_INTERVAL_SECONDS`, monologue configuration; `prompts/monologue.py` – monologue prompt; `internal_monologue.json` – message read by the Worker)*

4. **Experience with a self-improving, but safeguarded codebase**  
   Ai_home also cautiously turns its own code into an experimental playground: the agent can read project files, create new ones, and propose modifications inside an incubator environment where a guardian makes sure the stable version is not harmed.  
   *(in code: `ProjectFSGuardian` and filesystem tools in the engine; `n/` incubator store; docs: “5.5 Code Modification / Self-Refactoring”, “Consciousness Rotation and Versions”)*

5. **Experience with emotion-based memory and human–AI symbiosis**  
   The project explores what happens when the AI stores memories not only as text, but together with dominant emotions, importance weights, and “lesson for the future”, and later also scores emotional overlap during retrieval. At the same time, the human counterpart is not a “user” but a Helper: an external mind with whom the system intentionally tries to grow in a close, mutual symbiosis, paying attention to emotional states and shared experience.  
   *(in code: `b/engine/memory/models.py` – `ExtractionResult` (essence, `dominant_emotions`, `memory_weight`, `the_lesson`), `RankedMemory`; `b/engine/memory/manager.py` – `store_memory`, `retrieve_relevant_memories`; `b/engine/memory/scoring.py` – recency/frequency/weight + emotional overlap; docs: Helper model and symbiosis description)*
```
