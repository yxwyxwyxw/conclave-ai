from divination_fusion .models import FusionReport 
from divination_fusion .safety import apply_safety_policy 

def test_apply_safety_policy_softens_absolute_phrases ():
    report =FusionReport (
    summary ="你一定会在投资上成功",
    consensus_points =["这是绝对一致的判断"],
    disagreement_points =["局面注定如此"],
    reservations =[],
    suggested_followups =["你一定会需要评估医疗和投资风险"],
    raw_sections ={
    "结论摘要":"你一定会在投资上成功",
    "建议补充资料":["绝对不要忽视医疗"],
    "嵌套":{"note":"你一定会成功"},
    },
    )
    safe =apply_safety_policy (report )
    assert "一定会"not in safe .summary 
    assert all ("绝对"not in item for item in safe .consensus_points )
    assert all ("注定"not in item for item in safe .disagreement_points )
    assert "一定会"not in safe .raw_sections ["结论摘要"]
    assert "绝对"not in safe .raw_sections ["建议补充资料"][0 ]
    assert "一定会"not in safe .raw_sections ["嵌套"]["note"]
    assert "较可能"in safe .suggested_followups [0 ]
    assert any ("投资建议"in item for item in safe .reservations )
    assert any ("医疗建议"in item for item in safe .reservations )
