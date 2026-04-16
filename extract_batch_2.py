import csv

solutions = [
    ["Few-Shot Negative Examples", "Provide examples of typical hallucinations and explicitly mark them as 'INCORRECT' in the prompt", "Reddit /r/LocalLLM"],
    ["Explicit Critique Step", "Force a second LLM pass to 'Critique' the first answer for factual errors before final output", "GitHub Discussions"],
    ["Pydantic Schema Enforcement", "Use strict JSON schema validation to force the model to structure data, reducing prose-based fabrications", "StackOverflow"],
    ["Intermediate Tool Validation", "Verify tool outputs (e.g., API response 200 OK) before allowing the Agent to synthesize the answer", "GitHub Issues"],
    ["RAG 'Null' Option", "Instruct the retriever to return 'No relevant info found' to prevent the model from guessing based on weak similarity", "Reddit /r/LangChain"],
    ["Zero-Temperature Determinism", "Strictly set temperature=0 for factual queries to eliminate stochastic hallucination", "Medium AI Guides"],
    ["Multi-Agent Consensus", "Implement a 'Consensus' layer where 3 agents must agree on a fact before it is presented", "AutoGen Community"],
    ["Atomic Claim Verification", "Break the final response into a list of atoms and verify each one against the source doc", "arXiv/Practical Implementation"],
    ["External API Cross-Check", "Use a secondary, simpler API (e.g., Google Search API) to verify a specific entity name", "Developer Forums"],
    ["Context Noise Cleaning", "Implement a 'Context Pruner' to remove irrelevant retrieved chunks that might confuse the model", "Reddit /r/AutoGPT"],
    ["Manual CoVe Loop", "Implement a 'Generate $\rightarrow$ Question $\rightarrow$ Verify $\rightarrow$ Revise' loop in the agent state machine", "LangGraph Docs"],
    ["Dynamic Prompt Adaptation", "Change the system prompt's 'Strictness' level based on the detected query domain", "AI Dev Community"],
    ["High-Confidence HITL", "Trigger a 'Human-in-the-loop' request if the model's internal confidence is below 0.7", "Enterprise AI Implementations"],
    ["Contrastive Prompting", "Provide one correct and one hallucinated version of a similar task to highlight errors", "Reddit /r/LocalLLM"],
    ["Logit Bias Penalty", "Apply negative logit bias to common hallucination filler words (e.g., 'certainly', 'definitely')", "OpenAI Dev Forum"],
    ["Hierarchical RAG", "Summarize documents first $\rightarrow$ find relevant summary $\rightarrow$ retrieve specific detail", "Medium AI Engineering"],
    ["Majority Voting (Self-Consistency)", "Generate 3 responses at temp=0.7 and select the most common factual claim", "Google Research/Practical"],
    ["Pydantic Retry Loop", "If Pydantic validation fails $\rightarrow$ feed error back to LLM $\rightarrow$ regenerate until valid", "FastAPI/LLM integration"],
    ["Anti-Guessing System Prompt", "Add 'If you are unsure, you MUST say I don't know' as a high-priority instruction", "Common Practice"],
    ["Citation Anchor Verification", "Parse citations and physically check if the anchor text exists in the retrieved source", "GitHub / laion-ai"]
]

with open('/Users/KS/.openclaw/workspace/openclaw_hallucination_forum_solutions.csv', 'a', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerows(solutions)
