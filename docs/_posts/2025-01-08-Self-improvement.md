# AI rewriting its own code – self-improvement?

This issue should not be overblown. The current engine is at a stage where it failed to even copy its own code to the designated writable storage, let alone create anything meaningfully executable.

However, there are already observations:

* After reading its own code, it is capable of interpreting itself; I can have conversations with it about how it works.
* The context window of the Developer Mode gets so overloaded by the raw code that a change in strategy is likely needed. In the future, the system should not read the raw code, but only an abstract or structural description of it.
* I hit technical limitations with the code modification tools: experience shows that the LLM cannot reliably execute partial replacements (find & replace).
* It operates better by replacing full files, which is partly why an early refactoring was necessary to break the system down into many small files.
* However, replacing a full file is dangerous because it often happens that the new version contains the requested change, but something else has dropped out. Therefore, the modification tool will need to perform validation in the future: what was there, what became of it, and what was left out.

This requires complex development and is still a long way off. The theoretical concept of self-modification (the "born" versions and the incubator) is laid out in the identity section, but the practice is difficult. If anyone has experience in this area, I would be happy to hear from them.