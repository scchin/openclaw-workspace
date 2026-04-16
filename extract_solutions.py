import csv

solutions = [
    ["Uncertainty Quantification (UQLM)", "Use UQ-based detection to flag low-confidence outputs", "https://github.com/cvs-health/uqlm"],
    ["Dynamic Correction Decoding (Deco)", "Intervene in decoding process to correct hallucinations in real-time", "https://github.com/zjunlp/Deco"],
    ["Pluggable Context Layer (Agents.md)", "Maintain a live, repo-specific context layer to ground agent actions", "https://github.com/unoplat/unoplat-code-confluence"],
    ["Mask-DPO (ANAH)", "Use Masked-Direct Preference Optimization to align factual outputs", "https://github.com/open-compass/ANAH"],
    ["Image Retrieval Alignment (Re-Align)", "Leverage external image retrieval to anchor VLM descriptions", "https://github.com/taco-group/Re-Align"],
    ["Topological Concept Memory (FastMemory)", "Replace vectors with topological concept representations for 100% grounded RAG", "https://github.com/FastBuilderAI/memory"],
    ["Epistemic Uncertainty Unveiling (Uncertainty-o)", "Framework for revealing epistemic uncertainty in MLLMs", "https://github.com/Ruiyang-061X/Uncertainty-o"],
    ["Phrase-Level Alignment (HALVA)", "Data-augmented phrase-level alignment to mitigate object fabrication", "https://github.com/pritamqu/HALVA"],
    ["Associative Reasoning Control (FlexAC)", "Lightweight, training-free framework to modulate associative behavior", "https://github.com/ylhz/FlexAC"],
    ["Self-Optimizing Coherent Memory (Oscillink)", "Maintain coherent memory for embedding workflows to prevent drift", "https://github.com/Maverick0351a/Oscillink"],
    ["Listwise Preference Optimization (LPOI)", "Optimize VLM preferences specifically for factual accuracy", "https://github.com/fatemehpesaran310/lpoi"],
    ["Comprehensive VLM Hallucination List", "Curated collection of state-of-the-art detection and mitigation tools", "https://github.com/mala-lab/Awesome-LLM-LVLM-Hallucination-Detection-and-Mitigation"],
    ["Clinical Contrastive Decoding (CCD)", "Plug-and-play toolkit for radiology MLLM hallucination mitigation", "https://github.com/X-iZhang/CCD"],
    ["Adaptive Token Selection (HaMI)", "Robust detection via adaptive selection of tokens for verification", "https://github.com/mala-lab/HaMI"],
    ["Attention-Informed Token Boosting (PAINT)", "Intervene in self-attention to boost visual-attention informed tokens", "https://github.com/hasanar1f/PAINT"],
    ["Agentic RAG Framework (CoTARAG)", "Using agentic workflows to handle complex RAG without 'headaches'", "https://github.com/Kernel-Dirichlet/CoTARAG"],
    ["Verifiable Claim Extraction (Claimify)", "Extract decontextualized claims for independent groundedness checking", "https://github.com/deshwalmahesh/claimify"],
    ["Behavior-Oriented RL (BehaviorRL)", "Reinforce 'Learning When to Answer' to avoid guessing", "https://github.com/LLMSystems/BehaviorRL-Hallucination"],
    ["Citation Verification (DeepCitation)", "Stop hallucinations by verifying citations", "https://github.com/DeepCitation/deepcitation"],
    ["Semantic Tension (ΔS)", "Replacing confidence scores with 'semantic tension' to detect resistance to facts", "https://news.ycombinator.com/"]
]

with open('/Users/KS/.openclaw/workspace/openclaw_hallucination_forum_solutions.csv', 'a', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerows(solutions)
