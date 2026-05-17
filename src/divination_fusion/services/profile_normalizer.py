from __future__ import annotations 

from datetime import date ,datetime ,time ,timedelta ,timezone 
from typing import Optional ,Tuple ,Union 
from zoneinfo import ZoneInfo ,ZoneInfoNotFoundError 

from divination_fusion .models import AnalysisRequest ,DataCompleteness ,NormalizedProfile 

UTC =timezone .utc 

def normalize_profile (request :AnalysisRequest )->NormalizedProfile :
    profile =request .profile 
    missing_fields :list [str ]=[]
    notes :list [str ]=[]

    birth_date =_clean_optional_str (profile .birth_date )
    birth_time =_clean_optional_str (profile .birth_time )
    birth_place =_clean_optional_str (profile .birth_place )
    timezone_name =_clean_optional_str (profile .timezone )
    timezone_specified =timezone_name is not None 
    timezone_name =timezone_name or "UTC"

    if not birth_date :
        missing_fields .append ("birth_date")
    if not birth_time :
        missing_fields .append ("birth_time")
    if not birth_place :
        missing_fields .append ("birth_place")
    if not timezone_specified :
        missing_fields .append ("timezone")
        notes .append ("timezone_missing_defaulted_to_utc")

    tzinfo ,tz_note ,normalized_timezone ,timezone_is_fallback =_resolve_timezone (
    timezone_name ,
    timezone_specified ,
    )
    if tz_note :
        notes .append (tz_note )

    local_dt ,utc_dt ,completeness ,extra_missing ,extra_notes =_normalize_datetime (
    birth_date =birth_date ,
    birth_time =birth_time ,
    tzinfo =tzinfo ,
    timezone_is_fallback =timezone_is_fallback ,
    )
    missing_fields .extend (extra_missing )
    notes .extend (extra_notes )

    missing_fields =_dedupe_preserve_order (missing_fields )
    notes =_dedupe_preserve_order (notes )

    return NormalizedProfile (
    name =_clean_optional_str (profile .name ),
    timezone =normalized_timezone ,
    calendar =_clean_optional_str (profile .calendar )or "gregorian",
    birth_place =birth_place ,
    birth_datetime_local =local_dt ,
    birth_datetime_utc =utc_dt ,
    completeness =completeness ,
    missing_fields =missing_fields ,
    notes =notes ,
    )

def _normalize_datetime (
*,
birth_date :Optional [str ],
birth_time :Optional [str ],
tzinfo :Union [timezone ,ZoneInfo ],
timezone_is_fallback :bool ,
)->Tuple [Optional [str ],Optional [str ],DataCompleteness ,list [str ],list [str ]]:
    if not birth_date :
        return None ,None ,DataCompleteness .UNKNOWN ,["birth_date"],[]

    parsed_date =_parse_date (birth_date )
    if parsed_date is None :
        return None ,None ,DataCompleteness .UNKNOWN ,["birth_date"],["birth_date_unparseable"]

    if not birth_time :
        return (
        parsed_date .isoformat (),
        None ,
        DataCompleteness .DATE_ONLY ,
        ["birth_time"],
        ["birth_time_missing_used_date_only_normalization"],
        )

    parsed_time =_parse_time (birth_time )
    if parsed_time is None :
        return (
        parsed_date .isoformat (),
        None ,
        DataCompleteness .DATE_ONLY ,
        ["birth_time"],
        ["birth_time_unparseable"],
        )

    local_dt =datetime .combine (parsed_date ,parsed_time ).replace (tzinfo =tzinfo )
    utc_dt =local_dt .astimezone (UTC )
    completeness =DataCompleteness .ESTIMATED if timezone_is_fallback else DataCompleteness .EXACT 
    notes =["timezone_assumed_or_fell_back_to_utc"]if timezone_is_fallback else []
    return (
    local_dt .isoformat (),
    utc_dt .isoformat ().replace ("+00:00","Z"),
    completeness ,
    [],
    notes ,
    )

def _resolve_timezone (
timezone_name :str ,
timezone_specified :bool ,
)->Tuple [Union [timezone ,ZoneInfo ],Optional [str ],str ,bool ]:
    if timezone_name .upper ()=="UTC":
        return UTC ,None ,"UTC",not timezone_specified 

    try :
        zone =ZoneInfo (timezone_name )
        reference_dt =datetime (2024 ,1 ,1 ,tzinfo =zone )
        offset =reference_dt .utcoffset ()or timedelta (0 )
        return timezone (offset ),None ,timezone_name ,False 
    except ZoneInfoNotFoundError :
        return UTC ,"timezone_invalid_defaulted_to_utc","UTC",True 

def _parse_date (value :str )->Optional [date ]:
    try :
        return date .fromisoformat (value .strip ())
    except ValueError :
        return None 

def _parse_time (value :str )->Optional [time ]:
    normalized =value .strip ()
    if len (normalized )==5 and normalized .count (":")==1 :
        normalized =f"{normalized}:00"
    try :
        return time .fromisoformat (normalized )
    except ValueError :
        return None 

def _clean_optional_str (value :Optional [str ])->Optional [str ]:
    if value is None :
        return None 
    cleaned =value .strip ()
    return cleaned or None 

def _dedupe_preserve_order (values :list [str ])->list [str ]:
    seen :set [str ]=set ()
    result :list [str ]=[]
    for value in values :
        if value not in seen :
            seen .add (value )
            result .append (value )
    return result 
