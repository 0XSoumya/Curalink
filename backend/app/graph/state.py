from typing import TypedDict, List, Dict, Optional


class GraphState(TypedDict):
    query: str
    disease: Optional[str]
    location: Optional[str]

    parsed: Dict
    expanded_queries: List[str]

    retrieval_results: Dict

    top_docs: List[Dict]
    buffer_docs: List[Dict]

    clinical_trials: List[Dict]

    is_followup: bool
    needs_retrieval: bool

    session_id: str
    chat_history: List[Dict]

    final_output: Dict

    is_topic_shift: bool
    
    final_query: str