import operator
from typing import Annotated,TypedDict,Dict,List,Optional,Any

##defines schema for single compliance result
#error report
class ComplianceIssue(TypedDict):
    category:str
    description:str  ##Specific detail of violation
    severity:str  ##critical/warning
    timestamp:Optional[str]

##defines the global graph state
class VideoAuditState(TypedDict):
    """
    Defines the data schema for langgraph execution content
    """
    #input parameter
    video_url:str
    video_id:str

    #ingestion and extraction data
    local_file_path:Optional[str]
    video_metadata:dict[str,Any]  ## {"duration":15,"resolution":1080p}
    transcript:Optional[str]  ##speech to text
    ocr_text:list[str]

    ##analysis output
    compliance_results:Annotated[List[ComplianceIssue],operator.add]

    ##final output
    final_status:str  ##pass/fail
    final_report:str

    ##system level errors
    errors:Annotated[List[str],operator.add]

