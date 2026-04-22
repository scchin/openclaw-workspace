import json
import re
from typing import List, Dict, Tuple
from pydantic import BaseModel

class AtomicClaim(BaseModel):
    claim_id: int
    text: str
    status: str = "PENDING"  # SUPPORTED, CONTRADICTED, UNSUPPORTED
    evidence_snippet: str = ""

class VerificationResult(BaseModel):
    original_text: str
    claims: List[AtomicClaim]
    overall_score: float # 0.0 to 1.0
    hallucination_detected: bool

class L2Verifier:
    """L2 標準軌跡驗證器：實作原子化聲明比對"""
    
    def __init__(self, context: str):
        self.context = context

    def extract_claims(self, text: str) -> List[AtomicClaim]:
        """
        將文本拆解為原子事實。
        在實際生產環境中，這會調用一個專門的 Small-LLM。
        這裡實作一個基於句點/分號的基礎拆解邏輯作為物理佔位。
        """
        sentences = re.split(r'[。！\？;]', text)
        claims = []
        for i, s in enumerate(sentences):
            s = s.strip()
            if s:
                claims.append(AtomicClaim(claim_id=i+1, text=s))
        return claims

    def verify_claims(self, claims: List[AtomicClaim]) -> List[AtomicClaim]:
        """
        將原子聲明與物理上下文進行比對。
        邏輯：簡單的關鍵詞覆蓋度檢查 (物理近似) $\rightarrow$ 實際將由 LLM-Verifier 執行。
        """
        verified_claims = []
        for claim in claims:
            # 物理比對邏輯：檢查 claim 中的關鍵詞是否在 context 中出現
            # 這是一個簡化的物理模擬，實際運行時會調用 L2-Verifier-Agent
            keywords = [w for w in claim.text if len(w) > 1] 
            match_count = sum(1 for k in keywords if k in self.context)
            
            if match_count / max(len(keywords), 1) > 0.6:
                claim.status = "SUPPORTED"
                claim.evidence_snippet = "Found relevant keywords in context"
            elif match_count == 0:
                claim.status = "UNSUPPORTED"
            else:
                claim.status = "CONTRADICTED"
            
            verified_claims.append(claim)
        return verified_claims

    def run(self, text: str) -> VerificationResult:
        claims = self.extract_claims(text)
        verified = self.verify_claims(claims)
        
        supported_count = sum(1 for c in verified if c.status == "SUPPORTED")
        score = supported_count / max(len(verified), 1)
        
        return VerificationResult(
            original_text=text,
            claims=verified,
            overall_score=score,
            hallucination_detected=(score < 0.8)
        )

if __name__ == "__main__":
    ctx = "OpenClaw 是一個開源的 AI 助手框架，支持 DED 系統。它使用 Pydantic 進行意圖鎖定。"
    txt = "OpenClaw 是開源框架。它支持 DED。它使用 Pydantic 鎖定意圖。它能飛翔。"
    
    verifier = L2Verifier(ctx)
    res = verifier.run(txt)
    print(res.model_dump_json(indent=2))
