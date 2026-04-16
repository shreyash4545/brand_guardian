#FastAPI
import uuid
import logging
from fastapi import FastAPI ,HTTPException

from pydantic import BaseModel
from typing import List,Optional

#load env variables
from dotenv import load_dotenv
load_dotenv(override=True)

#initialize the telemetry(AZinsights)
from backend.source.api.AZinsights import setup_telemetry
setup_telemetry()

#importy langgraph
from backend.source.graph.workflow import app as compliance_graph

#config logging
logging.basicConfig(level=logging.INFO)

logger=logging.getLogger("api-server")

#fast api application
app=FastAPI(
    title=" Brand Guardian AI ",
    version="1.0.0"
)

#define data model(pydantic)
class AuditRequest(BaseModel):
    '''
    Defines expected structure for incoming api requests
    '''
    video_url:str

class ComplianceIssue(BaseModel):
    category:str
    description:str
    severity:str
class AuditResponse(BaseModel):
    video_id:str
    session_id:str
    status:str
    final_report:str
    compliance_results:List[ComplianceIssue]

#Define the main endpoint
@app.post("/audit",response_model=AuditResponse)

async def audit_video(request:AuditRequest):
    session_id=str(uuid.uuid4())
    video_id_short=f"vid_{session_id[:8]}"
    logger.info(f"Received the Audit request : {request.video_url} (Session : {session_id})")

    #graph inputs
    initial_inputs={
        "video_url":request.video_url,
        "video_id":video_id_short,
        "compliance_results":[],
        "errors":[]
    }

    try:
        final_state=compliance_graph.invoke(initial_inputs)
        return AuditResponse(
            session_id=session_id,
            video_id=final_state.get("video_id"),
            status=final_state.get("final_status","UNKNOWN"),
            final_report=final_state.get("final_report","NO REPORT GENERATED"),
            compliance_results=final_state.get("compliance_results",[])
        )
    except Exception as e:
        logger.error(f"Audit failed : {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Workflow Execution failed : {str(e)}"
        )

#api is working or not(health check)
@app.get("/health")

def health_check():
    return{"status": "healthy" , "service": "Brand guardian"}