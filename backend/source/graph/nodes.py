import json
import os
import logging
import re
from typing import Dict,Any,List
from langchain_openai import AzureChatOpenAI,AzureOpenAIEmbeddings
from langchain_community.vectorstores import AzureSearch
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage,HumanMessage

##Import states
from backend.source.graph.state import VideoAuditState,ComplianceIssue

##import service
from backend.source.services.video_indexer import VideoIndexerService

##config the logger
logger=logging.getLogger("brand-guardian")
logging.basicConfig(level=logging.INFO)


##NODE 1

def index_video_node(state:VideoAuditState)->Dict[str,Any]:

    '''
    Download yt video
    upload to azure video indexer
    extracts insights
    '''

    video_url=state.get("video_url")
    video_id_input=state.get("video_id","video_demo")
    logger.info(f"---[NODE:INDEXER] Processing:{video_url}")

    local_filename="temp_audit_video.mp4"
    try:
        vi_service=VideoIndexerService()

        ##downloads
        if "youtube.com" in video_url or "youtu.be" in video_url:
            local_path=vi_service.download_yt_video(video_url,output_path=local_filename)
        else:
            raise Exception("Please provide a valid link")

        ##upload
        azure_video_id=vi_service.upload_video(local_path,video_name=video_id_input)
        logger.info(f"Upload Success .Azure id :{azure_video_id}")

        ##cleaning
        if os.path.exists(local_path):
            os.remove(local_path)

        ##wait
        raw_insights=vi_service.wait_for_processing(azure_video_id)

        ##extract
        clean_data=vi_service.extract_data(raw_insights)
        logger.info("---[NODE:INDEXER] Extraction Completed---")
        return clean_data
    except Exception as e:
        logger.error(f"Video indexer failed:{e}")
        return{
            "errors":[str(e)],
            "final_status":"FAIL",
            "transcript":"",
            "ocr_text":[],
        }

#NODE : 2 Compliance auditor node
def audio_content_node(state:VideoAuditState)->Dict[str,Any]:
    '''
    Performs the RAG to audit the content
    '''

    logger.info(f"---[Node:Auditor] querying the knowledge base & llm")
    transcript=state.get("transcript","")
    if not transcript:
        logger.warning("No transcript available.Skipping the audit....")
        return{
            "final_status":"FAIL",
            "final_report":"Audit Skipped,No Transcript because video processing failed"
        }

    ##Initialize Azure services
    llm=AzureChatOpenAI(
        azure_deployment=os.getenv( "AZURE_OPENAI_CHAT_DEPLOYMENT"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        temperature = 0.0
    )
    embedding=AzureOpenAIEmbeddings(
        azure_deployment=os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY")
    )
    vector_store=AzureSearch(
        azure_search_endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
        azure_search_key=os.getenv("AZURE_SEARCH_API_KEY"),
        index_name=os.getenv("AZURE_SEARCH_INDEX_NAME"),
        embedding_function=embedding.embed_query
    )
    ##RAG Retrieval
    ocr_text=state.get("ocr_text",[])
    query_text=f"{transcript}{''.join(ocr_text)}"
    docs=vector_store.similarity_search(query_text,k=3)
    retrieved_rules="\n\n".join([doc.page_content for doc in docs])

    system_prompt=f"""You are a strict Senior Brand Compliance Auditor.
    Review the video content against the following official regulatory rules:
    {retrieved_rules}
    1. Analyze the transcript and on-screen text for any violations of these rules.
    2. Return your findings STRICTLY as a JSON object matching this exact structure:
    {{
            "output": "PASS" or "FAIL",
            "final_report": "A short summary of your overall findings.",
            "compliance_result": [
                {{
                    "category": "Claim Validation",
                    "description": "String detailing the exact violation",
                    "severity": "CRITICAL or WARNING"
                }}
            ]
        }}
        If no violations are found, set status to  "PASS" with  "compliance_result" list to[].
        Do NOT wrap the JSON in markdown code blocks
        """

    user_message=f"""
                Video_Metadata:{state.get('video_metadata',{})}
                Transcript:{transcript}
                OCR:{ocr_text}
                """
    try:
        response=llm.invoke(
            [SystemMessage(content=system_prompt),
             HumanMessage(content=user_message)]
        )
        content=response.content
        content= re.sub(r'^```json\s*', '',content)
        content= re.sub(r'\s*```$', '',content)
        audit_data=json.loads(content.strip())
        return{
            "compliance_results":audit_data.get("compliance_result",[]),
            "final_status":audit_data.get("output","FAIL"),
            "final_report":audit_data.get("final_report","No report generated")
        }
    except Exception as e:
        logger.error(f"System error in auditor node:{str(e)}")

        ##logging raw response
        logger.error(f"Raw LLM response:{response.content if 'response' in locals() else 'None'}")
        return{
            "errors":[str(e)],
            "Final_status":"FAIL"
        }