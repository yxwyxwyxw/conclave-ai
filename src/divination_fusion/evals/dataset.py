from __future__ import annotations 

from dataclasses import dataclass ,field 

from divination_fusion .agents import build_analysis_request 
from divination_fusion .models import AnalysisRequest 

@dataclass 
class EvalCase :
    case_id :str 
    request :AnalysisRequest 
    expected_focus_areas :list [str ]
    notes :str =""
    required_missing_fields :list [str ]=field (default_factory =list )
    required_issue_relations :dict [str ,str ]=field (default_factory =dict )
    required_followup_keywords :list [str ]=field (default_factory =list )
    required_reservation_keywords :list [str ]=field (default_factory =list )

def build_demo_dataset ()->list [EvalCase ]:
    return [
    EvalCase (
    case_id ="full-info-career-relationship",
    request =build_analysis_request (
    "请综合分析我的事业和感情趋势",
    name ="Demo One",
    birth_date ="1990-06-12",
    birth_time ="07:45",
    birth_place ="Shanghai",
    timezone ="Asia/Shanghai",
    ),
    expected_focus_areas =["career","relationship"],
    notes ="完整出生信息样本",
    required_issue_relations ={
    "career":"tension",
    "personality":"insufficient-data",
    "risk":"insufficient-data",
    },
    required_followup_keywords =["事业维度"],
    required_reservation_keywords =["存在无法裁决的 issue"],
    ),
    EvalCase (
    case_id ="date-only-health",
    request =build_analysis_request (
    "请看看健康和性格倾向",
    name ="Demo Two",
    birth_date ="1992-02-03",
    birth_place ="Hangzhou",
    timezone ="Asia/Shanghai",
    ),
    expected_focus_areas =["health","personality"],
    notes ="缺失时辰样本",
    required_missing_fields =["birth_time"],
    required_issue_relations ={
    "personality":"tension",
    "relationship":"insufficient-data",
    "career":"insufficient-data",
    "risk":"insufficient-data",
    },
    required_followup_keywords =["优先补充出生时辰","性格维度"],
    required_reservation_keywords =["存在无法裁决的 issue"],
    ),
    EvalCase (
    case_id ="career-tension-focus",
    request =build_analysis_request (
    "请重点分析我的事业走势",
    name ="Demo Three",
    birth_date ="1988-11-02",
    birth_time ="21:15",
    birth_place ="Beijing",
    timezone ="Asia/Shanghai",
    ),
    expected_focus_areas =["career"],
    notes ="聚焦单一维度但仍保留冲突追问的样本",
    required_issue_relations ={
    "career":"tension",
    "relationship":"insufficient-data",
    "personality":"insufficient-data",
    "risk":"insufficient-data",
    },
    required_followup_keywords =["事业维度"],
    required_reservation_keywords =["存在无法裁决的 issue"],
    ),
    ]
