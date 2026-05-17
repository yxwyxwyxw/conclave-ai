from divination_fusion .agents import build_analysis_request 

def test_build_analysis_request_infers_focus_areas ():
    request =build_analysis_request ("我想看事业和感情走势",birth_date ="1990-01-01")
    assert "career"in request .focus_areas 
    assert "relationship"in request .focus_areas 
