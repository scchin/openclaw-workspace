import csv

solutions = [
    ["Multi-Modal Cross-Verification", "Cross-check VLM output against a text-only LLM's interpretation of the same image metadata", "VLM Community / Practical"],
    ["Visual Grounding Markers", "Force the model to provide Bounding Box coordinates for every object it claims to see", "MLLM Best Practices"],
    ["Interleaving Retrieval and Generation", "Retrieve information incrementally as the answer is being generated, rather than once at the start", "Iterative RAG"],
    ["Fact-Checking Agent as a Middleware", "Insert a dedicated 'Verifier' Agent between the Generator and the Final Output", "Agentic Workflow Patterns"],
    ["Negative Constraint Prompting", "Explicitly list 'Common Hallucination Patterns' in the system prompt and forbid them", "Prompt Engineering Guides"],
    ["Confidence-Weighted Aggregation", "Generate multiple answers and weight them by the model's internal confidence scores", "Ensemble Methods"],
    ["Dynamic Prompt-Weighting", "Adjust the weight of the 'Truthfulness' instruction based on the complexity of the query", "Advanced Prompting"],
    ["Retrieval-Filtered Generation", "Filter out retrieved documents that have a low semantic similarity to the query *before* generation", "RAG Pipeline Optimization"],
    ["Human-in-the-loop (HITL) Trigger", "Trigger a human review if the agent's internal consistency score is below a threshold", "Enterprise Agent Workflows"],
    ["Self-Correction via Tool-Execution Errors", "Feed the exact error message from a failed tool call back to the LLM for a 'Self-Fix' attempt", "Coding Agent Patterns"],
    ["Recursive Summary-based RAG", "Build a hierarchy of summaries $\rightarrow$ Retrieve summary $\rightarrow$ Drill down to raw text", "Large-scale Document Analysis"],
    ["Semantic Tension Detection (ΔS)", "Implement a layer that detects when a model 'resists' a factual prompt", "Developer Forums / HN"],
    ["Symmetry Check (Translation-Back)", "Translate the answer to another language and back $\rightarrow$ check for factual drift", "Multilingual LLM Tips"],
    ["Constraint-Based Decoding", "Use a regex or grammar-based constraint to prevent the model from fabricating formats", "Guidance / Outlines"],
    ["Multi-Agent Debate for Fact-Checking", "Have two agents argue for and against a claim $\rightarrow$ a third agent decides the truth", "Multi-Agent Systems"],
    ["Knowledge-Graph Triplet Enforcement", "Force the model to output claims as (S, P, O) triplets for easier verification", "KG-LLM Integration"],
    ["External API Entity-Validation", "Automatically trigger a Wikipedia/Wikidata API call for any proper noun mentioned", "Fact-Checking Pipelines"],
    ["Context-Window Management", "Use 'Sliding Window' or 'Summarization' to prevent the 'lost-in-the-middle' hallucination", "Long-Context Optimization"],
    ["Truthfulness-Based Reward Shaping", "In fine-tuning, penalize 'confident but wrong' answers more heavily than 'unsure' answers", "RLHF Practical"],
    ["Zero-Shot CoT for Verification", "Force the model to explain 'Why this is true' before providing the final answer", "CoT Implementations"]
]

with open('/Users/KS/.openclaw/workspace/openclaw_hallucination_forum_solutions.csv', 'a', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerows(solutions)
