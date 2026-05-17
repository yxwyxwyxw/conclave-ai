from divination_fusion .text_debate import parse_round_control 

def test_parse_round_control_accepts_ascii_colon_and_status_variants ():
    payload =parse_round_control (
    "[回合裁定]\n"
    "当前状态: 建议结束当前争论\n"
    "裁判意见: 双方已经说到核心分歧。\n"
    "下一轮问题:\n"
    "终止原因: 已经足够清楚\n"
    )

    assert payload ["status"]=="结束"
    assert payload ["moderation"]=="双方已经说到核心分歧。"
    assert payload ["termination_reason"]=="已经足够清楚"

def test_parse_round_control_supports_multiline_moderation ():
    payload =parse_round_control (
    "[回合裁定]\n"
    "当前状态：继续\n"
    "裁判意见：请继续围绕 27 年财运。\n"
    "不要扩展到别的话题。\n"
    "下一轮问题：请直接回应对方对 27 年挣钱/亏欠的判断。\n"
    "终止原因：\n"
    )

    assert payload ["status"]=="继续"
    assert payload ["moderation"]=="请继续围绕 27 年财运。\n不要扩展到别的话题。"
    assert payload ["next_question"]=="请直接回应对方对 27 年挣钱/亏欠的判断。"
