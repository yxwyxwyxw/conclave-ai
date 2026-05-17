from __future__ import annotations 

from datetime import datetime 
from hashlib import sha1 
import re 
from typing import Optional 

from divination_fusion .models import (
AnalysisRequest ,
Claim ,
DataCompleteness ,
NormalizedProfile ,
SystemEvidence ,
)

DIMENSIONS =("personality","career","relationship","risk")
DIMENSION_LABELS ={
"personality":"性格",
"career":"事业",
"relationship":"感情",
"risk":"风险",
}
SEASON_LABELS ={
"winter":"冬季",
"spring":"春季",
"summer":"夏季",
"autumn":"秋季",
"unknown":"未知季节",
}
TIME_BAND_LABELS ={
"morning":"上午",
"midday":"中午",
"afternoon":"下午",
"evening":"傍晚",
"night":"夜间",
"unknown":"未知时段",
}
DAY_TYPE_LABELS ={
"even":"偶数日",
"odd":"奇数日",
"unknown":"未知日期",
}
COMPLETENESS_LABELS ={
DataCompleteness .EXACT :"完整",
DataCompleteness .ESTIMATED :"估计",
DataCompleteness .DATE_ONLY :"仅日期",
DataCompleteness .UNKNOWN :"未知",
}
__all__ =["analyze_bazi"]

def analyze_bazi (request :AnalysisRequest ,profile :NormalizedProfile )->SystemEvidence :
    """Build a deterministic v1 Bazi evidence bundle.

    The implementation is intentionally heuristic: it creates structured claims
    from normalized profile features so downstream conflict detection can operate
    on stable ids and consistent dimensions without requiring a real calendar
    engine yet.
    """

    features =_profile_features (profile )
    focus =set (request .focus_areas or [])
    claims :list [Claim ]=[]
    warnings :list [str ]=[]

    if profile .completeness !=DataCompleteness .EXACT :
        warnings .append (_completeness_warning (profile .completeness ))
    if profile .birth_datetime_local is None :
        warnings .append ("出生时间不可用，时辰敏感的判断会转为更保守的口径。")
    if profile .birth_datetime_utc is None :
        warnings .append ("UTC 转换不可用，跨时区回放时只能近似处理。")

    for dimension in DIMENSIONS :
        if focus and dimension not in focus and dimension !="risk":
            continue 
        claim =_build_claim (request ,profile ,dimension ,features )
        claims .append (claim )

    if not claims :
        claims .append (_build_claim (request ,profile ,"personality",features ))

    summary =_build_summary (profile ,claims )
    data_quality =_data_quality_score (profile )
    if data_quality <0.7 :
        warnings .append ("数据质量有限，当前证据只能先按暂定结果看。")

    return SystemEvidence (
    system ="bazi",
    summary =summary ,
    claims =claims ,
    data_quality =data_quality ,
    warnings =warnings ,
    )

def _build_claim (
request :AnalysisRequest ,
profile :NormalizedProfile ,
dimension :str ,
features :dict [str ,str ],
)->Claim :
    statement =_statement_for_dimension (dimension ,features )
    evidence =_evidence_for_dimension (request ,profile ,dimension ,features )
    claim_id =_stable_claim_id (profile ,dimension ,statement ,evidence )
    depends_on =_dependencies (profile )
    qualifiers =_qualifiers (profile ,dimension )
    return Claim (
    claim_id =claim_id ,
    system ="bazi",
    dimension =dimension ,
    statement =statement ,
    evidence =evidence ,
    depends_on =depends_on ,
    qualifiers =qualifiers ,
    )

def _profile_features (profile :NormalizedProfile )->dict [str ,str ]:
    features :dict [str ,str ]={
    "season":"unknown",
    "time_band":"unknown",
    "day_type":"unknown",
    "completeness":profile .completeness .value ,
    }
    if profile .birth_datetime_local :
        parsed =_parse_datetime (profile .birth_datetime_local )
        if parsed is not None :
            month =parsed .month 
            features ["season"]=_season_from_month (month )
            features ["time_band"]=_time_band (parsed .hour )
            features ["day_type"]="even"if parsed .day %2 ==0 else "odd"
    return features 

def _parse_datetime (value :str )->Optional [datetime ]:
    candidates =(
    value ,
    value .replace ("Z","+00:00"),
    value .replace (" ","T"),
    )
    for candidate in candidates :
        try :
            return datetime .fromisoformat (candidate )
        except ValueError :
            continue 
    match =re .match (
    r"^(?P<date>\d{4}-\d{2}-\d{2})(?:[ T](?P<hour>\d{2}):(?P<minute>\d{2}))?$",
    value ,
    )
    if match :
        year ,month ,day =map (int ,match .group ("date").split ("-"))
        hour =int (match .group ("hour")or 12 )
        minute =int (match .group ("minute")or 0 )
        return datetime (year ,month ,day ,hour ,minute )
    return None 

def _season_from_month (month :int )->str :
    if month in (12 ,1 ,2 ):
        return "winter"
    if month in (3 ,4 ,5 ):
        return "spring"
    if month in (6 ,7 ,8 ):
        return "summer"
    return "autumn"

def _time_band (hour :int )->str :
    if 5 <=hour <11 :
        return "morning"
    if 11 <=hour <14 :
        return "midday"
    if 14 <=hour <18 :
        return "afternoon"
    if 18 <=hour <22 :
        return "evening"
    return "night"

def _statement_for_dimension (dimension :str ,features :dict [str ,str ])->str :
    season =SEASON_LABELS [features ["season"]]
    time_band =TIME_BAND_LABELS [features ["time_band"]]
    day_type =DAY_TYPE_LABELS [features ["day_type"]]
    templates ={
    "personality":f"性格主线更偏向稳住节奏、慢慢校准，带有{season}气质和{time_band}能量。",
    "career":f"事业发展更适合累积推进，尤其在{time_band}节奏里更容易看见结构感。",
    "relationship":f"感情和关系处理更看重边界与稳定，整体带有{season}气场，也更强调{day_type}的持续性。",
    "risk":"风险侧主要提示资料不全会放大误差，当前更需要防的是缺失信息带来的判断偏差。",
    }
    return templates [dimension ]

def _evidence_for_dimension (
request :AnalysisRequest ,
profile :NormalizedProfile ,
dimension :str ,
features :dict [str ,str ],
)->list [str ]:
    evidence =[
    f"关注领域：{_join_focus_areas(request.focus_areas)}",
    f"画像完整度：{COMPLETENESS_LABELS[profile.completeness]}",
    f"季节特征：{SEASON_LABELS[features['season']]}",
    f"时间段：{TIME_BAND_LABELS[features['time_band']]}",
    ]
    if profile .birth_place :
        evidence .append (f"出生地：{profile.birth_place}")
    if dimension =="risk":
        evidence .append ("风险依据：主要看画像完整度和缺失项")
    return evidence 

def _data_quality_score (profile :NormalizedProfile )->float :
    score ={
    DataCompleteness .EXACT :0.9 ,
    DataCompleteness .ESTIMATED :0.75 ,
    DataCompleteness .DATE_ONLY :0.6 ,
    DataCompleteness .UNKNOWN :0.45 ,
    }[profile .completeness ]
    if profile .birth_datetime_local is None :
        score -=0.08 
    if profile .birth_datetime_utc is None :
        score -=0.03 
    if profile .timezone =="UTC":
        score +=0.02 
    return round (max (0.0 ,min (1.0 ,score )),2 )

def _stable_claim_id (
profile :NormalizedProfile ,
dimension :str ,
statement :str ,
evidence :list [str ],
)->str :
    payload ="|".join (
    [
    "bazi",
    dimension ,
    profile .name or "",
    profile .birth_datetime_local or "",
    profile .birth_datetime_utc or "",
    statement ,
    "::".join (evidence ),
    ]
    )
    digest =sha1 (payload .encode ("utf-8")).hexdigest ()[:12 ]
    return f"bazi-{dimension}-{digest}"

def _dependencies (profile :NormalizedProfile )->list [str ]:
    deps =["归一化画像"]
    if profile .birth_datetime_local is None :
        deps .append ("缺少出生时辰")
    if profile .birth_datetime_utc is None :
        deps .append ("缺少 UTC 时间")
    return deps 

def _qualifiers (profile :NormalizedProfile ,dimension :str )->list [str ]:
    qualifiers =[f"历法={profile.calendar}"]
    if profile .birth_datetime_local is None :
        qualifiers .append ("时辰敏感")
    if dimension =="risk":
        qualifiers .append ("风险元判断")
    return qualifiers 

def _completeness_warning (completeness :DataCompleteness )->str :
    return {
    DataCompleteness .EXACT :"画像标记为完整，但仍建议保留基本审慎。",
    DataCompleteness .ESTIMATED :"画像里包含估计字段，精度会比完整资料更低。",
    DataCompleteness .DATE_ONLY :"目前只有出生日期，时辰相关判断会被明显收紧。",
    DataCompleteness .UNKNOWN :"画像完整度未知，当前所有主张都只能按暂定结果处理。",
    }[completeness ]

def _build_summary (profile :NormalizedProfile ,claims :list [Claim ])->str :
    subject =profile .name or "匿名画像"
    completeness =COMPLETENESS_LABELS [profile .completeness ]
    return f"八字侧为{subject}生成了{len(claims)}条结构化主张，画像完整度为{completeness}。"

def _join_focus_areas (focus_areas :list [str ])->str :
    if not focus_areas :
        return "无"
    labels =[DIMENSION_LABELS .get (area ,area )for area in focus_areas ]
    return "、".join (labels )
