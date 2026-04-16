import csv

solutions = [
    ["HyDE (Hypothetical Document Embeddings)", "Generate a hypothetical answer first, then use it as the query for retrieval to improve hit rate", "RAG Community / Practical Guides"],
    ["Parent-Document Retrieval", "Retrieve small chunks for precision but pass larger parent contexts to the LLM for better understanding", "LangChain / GitHub"],
    ["Re-Ranking Step (Cross-Encoders)", "Retrieve 100 docs via vector search, then use a Cross-Encoder to pick the top 5 most relevant ones", "Pinecone / Weaviate Forums"],
    ["Query Expansion (Multi-Query)", "Generate 3 variations of the user query to capture a wider range of relevant documents", "RAG Best Practices"],
    ["Self-RAG", "Train the model to output special tokens ([Retrieve], [IsSupported]) to control its own RAG process", "Research Implementation"],
    ["Plan-and-Execute Pattern", "Decouple planning from execution; verify the plan before executing any tool call", "BabyAGI / AutoGPT"],
    ["Reflection-Loop (Self-Critique)", "After generation, prompt the model to find its own factual errors and rewrite", "Reflexion / GitHub"],
    ["Knowledge-Graph Anchoring", "Convert retrieved text to triplets and verify the path between entities", "Neo4j / LLM Integration"],
    ["Few-Shot Negative Prompting", "Include examples of 'Common Hallucinations' in the prompt and mark them as 'FAIL'", "Reddit /r/LocalLLM"],
    ["Strict Grounding Constraint", "Instruction: 'Only use provided context. If not found, say I don't know. DO NOT use internal knowledge'", "General Best Practice"],
    ["Multi-Step Verification Chain", "Break a long answer into 5 claims $\rightarrow$ verify each $\rightarrow$ merge into final answer", "LangGraph / Practical"],
    ["Confidence Scoring via Logits", "Calculate the average log-probability of factual tokens to trigger a human-in-the-loop review", "OpenAI API / Dev Forums"],
    ["External API Fact-Checking", "For entities (dates, names), trigger a mandatory API call to a trusted source (e.g., Wikidata)", "Enterprise Agent Patterns"],
    ["Context Pruning", "Remove the most dissimilar retrieved chunks to prevent 'lost in the middle' hallucinations", "Anthropic / Long-Context Guides"],
    ["Chain-of-Verification (CoVe)", "Draft $\rightarrow$ Question Generation $\rightarrow$ Independent Verification $\rightarrow$ Final Revision", "Meta AI / Practical"],
    ["Prompt-based Uncertainty Expression", "Instruct the model to use phrases like 'I am reasonably sure' or 'I am unsure' based on evidence", "TruthfulQA Implementations"],
    ["Recursive Summary-based Retrieval", "Create a hierarchy of summaries $\rightarrow$ retrieve summary $\rightarrow$ drill down to raw text", "Large-scale Doc Analysis"],
    ["Negative Constraint Enforcement", "List specific things the model MUST NOT say (e.g., 'I am an AI', 'As a language model')", "System Prompt Tuning"],
    ["Iterative Tool-Call Refinement", "If a tool returns an error or 'no results', force the agent to rewrite the query and try again", "Agentic Workflow Patterns"],
    ["Cross-Model Consistency Check", "Compare the output of a 70B model with a 7B model; discrepancies flag potential hallucinations", "Model Distillation / Verification"]
]

with open('/Users/KS/.openclaw/workspace/openclaw_hallucination_forum_solutions.csv', 'a', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerows(solutions)
