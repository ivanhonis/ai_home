# Initiative

This is the hardest task of all. There are several reasons for this, but two stand out:

1. The system is driven by LLMs, and there is not a crumb of initiative in these models. This stems primarily from the architecture itself: a question goes in, an answer comes out, and the system stops. If the user does not initiate, there is no interaction. "Intelligence" is active only at the moment of generation.
2. There is no time component. The model does not feel the passage of time.

It is very difficult to force initiative onto this passive architecture. Yet, what elements am I currently trying?

The tools are processed by a Worker, and it has the option to use a tool called `flow.continue`. This results in the system theoretically being able to stay in flow: if it specifies tools in a way that it executes something and then calls `continue`, it can keep the initiative. Since the Helper and the AI can communicate in parallel within the system, this does not take away the opportunity for the Helper to intervene.

Furthermore, there is a Proactive Thread, which gives the system a chance at periodic intervals: "If you want to do something, you can do it now."

**Observation:**
After several rounds of practice and explanation, the system is able to form an image of the essence of `continue`. It is capable of building complex processes from it: it switched to another mode, wrote into a file, came back to General mode, and then stopped and told me what it did.
However, typically it does *not* initiate, but asks. "What would you say if I did this?" – it seeks permission for the step rather than taking it.

**Thought:**
Independent initiative is a double-edged sword. It depends on what it does!
The safety of autonomy lies in the saved memories, the core identity, and the precise understanding of the task. If these slip, the action can slip as well. The Monologue (the internal "subconscious") can help in controlling this, but only if it does not feed on exactly the same information as the acting self, but has an external perspective.