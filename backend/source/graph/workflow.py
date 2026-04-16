'''
This module defines the DAG:Directed acyclic graph that orchestrates the video compliance audit process.
It connects the nodes using StateGraph from langgraph.
START-> index_video_node-> audit_content_node-> END
'''
from langgraph.graph import StateGraph,END,START
from backend.source.graph.state import VideoAuditState

from backend.source.graph.nodes import(
    index_video_node,
    audio_content_node
)

def create_graph ():
    '''
    Constructs and compiles the langgraph workflow.
    Returns:
    Compiled graph,runnable graph object for execution
    '''

    #initialize the graph with state graph
    workflow=StateGraph(VideoAuditState)

    #add nodes
    workflow.add_node("indexer",index_video_node)
    workflow.add_node("auditor",audio_content_node)

    #entry point
    workflow.set_entry_point("indexer")

    #add edges
    workflow.add_edge("indexer","auditor")
    workflow.add_edge("auditor",END)

    app=workflow.compile()
    return app

#expose the function
app=create_graph()
