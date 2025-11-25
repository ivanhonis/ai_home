# How my Monologue thread works

In my architecture the `Monologue` thread is a background process that models an inner voice – almost like a subconscious layer. It never talks directly to the user. It just observes, reflects, and sends short hints to the `Worker`.

## 1. Watching the global log

Every message in the system (user, assistant, tool) is not only stored in the room’s own context, but also appended to a global log.

The `Monologue` thread simply watches this global log.
When it notices that the file has changed (something happened), it wakes up and runs a cycle.

## 2. Loading the context

When a change is detected, the `Monologue` thread loads:

- the relevant part of the global log (usually the recent history, not everything),
- the identity / persona (who “I” am as an agent),
- previous monologue notes, if there are any.

This gives it both short-term and longer-term context.

## 3. Calling the LLM for reflection

From this input it builds a prompt and calls the LLM.
The goal here is **not** to answer the user, but to:

- understand what is going on over a longer time scale,
- look for patterns,
- extract a few concrete lessons or directions.

From the LLM I usually ask for three things:

1. A longer **reflection** text
   – what’s going on, what I might be learning, what to pay attention to.

2. A short **`message_to_worker`**
   – a few sentences of very direct guidance that the `Worker` can use right away.

3. Optionally, a deeper **monologue memory entry**
   – something like a distilled observation that might matter later.

## 4. Saving the outputs

I handle the outputs differently:

- The longer reflection and any deep monologue memories are stored separately.
  These are mainly for analysis and future tuning.

- The short `message_to_worker` is written into a small file
  (for example `internal_monologue.json`) that the `Worker` reads every cycle.

This small message is what becomes the active “whisper” to the `Worker`.

## 5. How it influences the Worker

When the `Worker` thinks about a reply, it doesn’t only see:

- the current room context,
- the relevant long-term memories,

but also the fresh monologue message.

I inject that short message into the system prompt, so it acts like a quiet internal suggestion: what to be careful about, what direction to prefer, what to prioritize.

The user never sees this explicitly. It shapes the behaviour from the inside.

## 6. Continuous presence, not Q→A

The `Monologue` thread does not block anything and is not tied to a strict “question → answer” loop. It is more like a continuous presence:

- it watches what happens,
- occasionally reflects,
- and feeds short intuitions back to the `Worker`.

This way the `Monologue` really behaves like a kind of subconscious: it evaluates the situation in the background and tries to support the system with small insights and ideas, without ever talking to the user directly.
