from pydantic import BaseModel, Field
from typing import List, Optional, Any
import json
import os
from datetime import datetime

class ExecutionStep(BaseModel):
    step_id: int
    action: str = Field(..., description="具體要執行的動作")
    tool: str = Field(..., description="使用的工具名稱")
    expected_evidence: str = Field(..., description="執行後應看到的物理證據（例如：文件內容、API 回傳值、編譯通過）")
    verification_method: str = Field(..., description="驗證證據的方式 (例如: regex, exact_match, llm_verify)")

class ExecutionPlan(BaseModel):
    plan_id: str
    objective: str = Field(..., description="本次執行的終極目標")
    priority: str = Field("Standard", description="L1/L2/L3 級別")
    steps: List[ExecutionStep]
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    status: str = "PENDING" # PENDING, EXECUTING, COMPLETED, FAILED

PLAN_FILE = "/Users/KS/.openclaw/workspace/current_plan.json"

def lock_intent(plan: ExecutionPlan):
    """將意圖物理鎖定至文件"""
    with open(PLAN_FILE, 'w', encoding='utf-8') as f:
        f.write(plan.model_dump_json(indent=2))
    return f"Intent locked to {PLAN_FILE}"

def load_plan() -> Optional[ExecutionPlan]:
    """加載當前鎖定的計畫"""
    if not os.path.exists(PLAN_FILE):
        return None
    with open(PLAN_FILE, 'r', encoding='utf-8') as f:
        return ExecutionPlan.model_validate_json(f.read())

def update_step_status(step_id: int, status: str, actual_evidence: str):
    """更新步驟執行狀態與實測證據"""
    plan = load_plan()
    if not plan:
        return "No plan found"
    
    for step in plan.steps:
        if step.step_id == step_id:
            # 在實際實作中，我們會將 evidence 儲存在一個獨立的 trajectory_log.json 中
            # 這裡先做簡單的狀態紀錄
            pass
    
    # 為了保持物理軌跡，我們建議將每一步的輸出直接 append 到一個 log 文件
    with open("/Users/KS/.openclaw/workspace/trajectory_log.jsonl", 'a', encoding='utf-8') as f:
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "step_id": step_id,
            "status": status,
            "actual_evidence": actual_evidence
        }
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    
    return f"Step {step_id} logged."

if __name__ == "__main__":
    # 測試用
    test_plan = ExecutionPlan(
        plan_id="test-001",
        objective="驗證 Pydantic 鎖定機制",
        steps=[
            ExecutionStep(step_id=1, action="讀取文件", tool="read", expected_evidence="文件內容存在", verification_method="existence")
        ]
    )
    print(lock_intent(test_plan))
