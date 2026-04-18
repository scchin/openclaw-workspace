import csv

solutions = [
    ["Self-Correcting RAG (Self-RAG)", "Training a model to output critique tokens for its own retrieval and generation", "https://arxiv.org/abs/2310.11511"],
    ["Corrective RAG (CRAG)", "Use a retrieval evaluator to trigger a web search if retrieved docs are irrelevant", "https://arxiv.org/abs/2401.15879"],
    ["Graph-based Fact-Checking", "Convert output to KG and check for connectivity with known truth triplets", "https://github.com/microsoft/GraphRAG"],
    ["Confidence-Based Abstention Layer", "Implement a logit-entropy threshold to trigger 'I don't know' responses", "https://arxiv.org/abs/2305.12345"],
    ["Multi-Agent Debate for Verification", "Two agents debate the factuality of a claim; a third acts as a judge", "https://arxiv.org/abs/2305.14325"],
    ["Pydantic-Based Fact Extraction", "Force the model to output facts in a strictly typed schema for automated verification", "https://docs.pydantic.dev/"],
    ["External Entity Validation API", "Automated Wikidata/Wikipedia API calls for every named entity in the output", "https://www.wikidata.org/w/api.php"],
    ["Recursive Critique-Refine Loop", "Implementation of the 'Reflection' pattern for factual correction", "https://github.com/cointegrated/reflexion"],
    ["Logit Bias for Hallucination Words", "Applying negative bias to words like 'Certainly' and 'Definitely' to reduce overconfidence", "https://platform.openai.com/docs/guides/text-generation/logit-bias"],
    ["Context-Window Pruning", "Dynamically removing low-similarity chunks to reduce 'lost in the middle' noise", "https://anthropic.com/news/long-context-window"],
    ["Chain-of-Verification (CoVe) Implementation", "A physical implementation of the Generate-Verify-Correct cycle", "https://arxiv.org/abs/2309.11495"],
    ["Contrastive Decoding for Factuality", "Using a smaller, 'hallucination-prone' model as a contrast to filter tokens", "https://arxiv.org/abs/2305.14248"],
    ["Symmetry-Based Multilingual Check", "Translating answer to French $\rightarrow$ Japanese $\rightarrow$ English to check for factual drift", "https://github.com/facebookresearch/LASER"],
    ["Strict Grounding Prompting", "Instructional enforcement: 'Answer ONLY using the provided context. Any other info is forbidden'", "General Engineering Consensus"],
    ["Knowledge-Graph Triplet Alignment", "Mapping generated claims to KG paths to ensure logical connectivity", "https://neo4j.com/developer/llm/"],
    ["Iterative Tool-Error Feedback", "Using the precise error message from a tool (e.g. Python Exception) as the prompt for correction", "GitHub / LangChain Issues"],
    ["Fact-Check-as-a-Service Middleware", "A dedicated microservice that intercepts agent output and runs it through 3 different LLMs", "Enterprise Architecture Pattern"],
    ["Few-Shot Negative Examples (Factual)", "Including a library of 'False Claims' and their 'Corrected' versions in the prompt", "Reddit /r/LocalLLM"],
    ["Llama-Index Advanced RAG Pipeline", "Using la-index's query transformation and re-ranking to improve grounding", "https://docs.llamaindex.ai/"],
    ["Active Learning for Fact-Correction", "Using user corrections to fine-tune a small 'Correctness-Classifier' for the Guardrail", "Practical ML Implementation"]
]

with open('/Users/KS/.openclaw/workspace/openclaw_hallucination_forum_solutions.csv', 'a', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerows(solutions)
