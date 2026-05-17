from divination_fusion .prompts import analyzer_system_prompt ,battler_system_prompt ,judge_system_prompt 

def test_analyzer_prompts_are_system_specific ():
    bazi_prompt =analyzer_system_prompt ("bazi")
    astrology_prompt =analyzer_system_prompt ("astrology")

    assert "八字命理分析员"in bazi_prompt 
    assert "不要借用紫微斗数、占星术语"in bazi_prompt 
    assert "西方占星分析员"in astrology_prompt 
    assert "不要借用八字、紫微术语"in astrology_prompt 
    assert bazi_prompt !=astrology_prompt 

def test_battler_prompts_are_system_specific ():
    bazi_prompt =battler_system_prompt ("bazi")
    astrology_prompt =battler_system_prompt ("astrology")

    assert "八字流派辩手"in bazi_prompt 
    assert "西方占星流派辩手"in astrology_prompt 
    assert "只回应裁判发问"in bazi_prompt 
    assert bazi_prompt !=astrology_prompt 

def test_judge_prompt_keeps_structured_adjudication_boundary ():
    prompt =judge_system_prompt ()

    assert "争点发现"in prompt 
    assert "回合控题"in prompt 
    assert "不要输出 JSON"in prompt 
