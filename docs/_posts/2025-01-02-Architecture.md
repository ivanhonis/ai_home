# My four-thread architecture

In this architecture I use four main threads: `Input`, `Worker`, `Memory`, and `Monologue`.

## Input – handling raw stimuli

The `Input` thread handles incoming stimuli.
It prints the prompt, reads whatever I type, and pushes it into a queue for the main logic.
It doesn’t interpret or decide anything, it just lets information into the system.

## Worker – the thinking layer

The `Worker` thread is the thinking layer.
It takes over tasks (user messages, tool results), assembles:

- the current context,
- the relevant memories,
- the internal monologue message,

and based on all that it calls the LLM.
The actual reply and any tool calls are produced here.

## Memory – long-term memory

The `Memory` thread is the long-term memory.
It automatically watches the current situation and new messages, and based on the context it generates “memory images”:

- it decides what’s important,
- stores those pieces in a structured way (with embeddings),
- later it can return similar past situations to the `Worker`,

so the `Worker` doesn’t have to rely only on the fresh log.

## Monologue – inner voice / subconscious

The `Monologue` thread is the inner voice, essentially a subconscious layer.
It watches a global log, evaluates the situation, tries to spot patterns, and from time to time it supports the `Worker` with short insights and ideas.

These inner messages never appear directly in the user-facing output; they show up indirectly as background intuition in the system prompt.

## Continuous presence instead of Q→A

Taken together, this does not behave like a classic question → answer interaction, but more like a continuous presence:

- the `Input` + `Worker` threads continuously process incoming stimuli,
- the `Monologue` reflects on them in a subconscious way and suggests directions,
- the `Memory` thread automatically builds and returns memory images that match the current situation.

This is how I get from simple Q→A towards a system that is always “there” and processing what happens.
