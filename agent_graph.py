import os
import requests
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt
from langchain_mistralai import ChatMistralAI
from dotenv import load_dotenv

load_dotenv()

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
writer_llm = ChatMistralAI(model="mistral-large-latest", api_key=MISTRAL_API_KEY, temperature=0.7)

class State(TypedDict):
    topic: str
    draft: str
    review_feedback: str
    is_approved: bool
    attempt: int
    api_status: str

WRITER_SYSTEM_PROMPT = (
    "You are an expert LinkedIn content writer. Write engaging, professional LinkedIn posts.\n"
    "Rules:\n"
    "- Strong hook in the first line\n"
    "- One clear takeaway\n"
    "- Easy to skim with short paragraphs (roughly 150-200 words)\n"
    "- End with an engaging question or CTA\n"
    "- Strictly NO hashtags.\n"
    "If feedback is provided, modify the previous draft to address all points."
)

def writer_node(state: State) -> dict:
    attempt = state.get("attempt", 0) + 1
    topic = state["topic"]
    previous_feedback = state.get("review_feedback", "")

    if attempt == 1:
        user_message = f"Write a LinkedIn post on this topic: {topic}"
    else:
        user_message = (
            f"Your previous draft on '{topic}' was rejected.\n\n"
            f"Reviewer feedback:\n{previous_feedback}\n\n"
            f"Write a NEW improved LinkedIn post that fixes every issue mentioned."
        )

    messages = [("system", WRITER_SYSTEM_PROMPT), ("human", user_message)]
    response = writer_llm.invoke(messages)

    return {"draft": response.content, "attempt": attempt}

def human_review_node(state: State) -> dict:
    human_response = interrupt({
        "draft": state["draft"],
        "attempt": state["attempt"],
        "instruction": "Approve to post on LinkedIn, or give feedback to rewrite."
    })

    response = str(human_response).strip()
    if response.lower() in ["approved", "approve"]:
        return {"is_approved": True, "review_feedback": "Approved by human."}
    else:
        return {"is_approved": False, "review_feedback": response}

def post_to_linkedin_node(state: State) -> dict:
    access_token = os.getenv("LINKEDIN_ACCESS_TOKEN")
    if not access_token:
        return {"api_status": "❌ LinkedIn Access Token missing!"}

    me_url = "https://api.linkedin.com/v2/userinfo"
    headers = {"Authorization": f"Bearer {access_token}"}

    try:
        me_response = requests.get(me_url, headers=headers, timeout=15)
        if me_response.status_code != 200:
            return {"api_status": f"❌ Profile fetch failed: {me_response.text}"}

        user_data = me_response.json()
        person_id = user_data.get("sub")
        if not person_id:
            return {"api_status": "❌ Profile ID missing in LinkedIn response."}
        author_urn = f"urn:li:person:{person_id}"
    except Exception as e:
        return {"api_status": f"❌ Exception on profile fetch: {str(e)}"}

    post_url = "https://api.linkedin.com/rest/posts"
    post_headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0",
        "LinkedIn-Version": "202502"
    }

    payload = {
        "author": author_urn,
        "commentary": state["draft"],
        "visibility": "PUBLIC",
        "distribution": {"feedDistribution": "MAIN_FEED", "targetEntities": []},
        "lifecycleState": "PUBLISHED"
    }

    try:
        response = requests.post(post_url, headers=post_headers, json=payload, timeout=30)
        if response.status_code in (200, 201):
            return {"api_status": f"🚀 Successfully posted to Personal Profile ({author_urn})!"}
        return {"api_status": f"❌ API Error ({response.status_code}): {response.text}"}
    except requests.exceptions.RequestException as e:
        return {"api_status": f"❌ Request failed: {str(e)}"}

def should_stop_looping(state: State):
    if state.get('is_approved'):
        return "post_to_linkedin"
    if state.get('attempt', 0) >= 3:
        return "end_workflow"
    return "writer"

graph = StateGraph(State)
graph.add_node("writer", writer_node)
graph.add_node("human_review", human_review_node)
graph.add_node("post_to_linkedin", post_to_linkedin_node)

graph.add_edge(START, "writer")
graph.add_edge("writer", "human_review")

graph.add_conditional_edges(
    "human_review",
    should_stop_looping,
    {"writer": "writer", "post_to_linkedin": "post_to_linkedin", "end_workflow": END}
)

graph.add_edge("post_to_linkedin", END)
checkpointer = MemorySaver()
agent_app = graph.compile(checkpointer=checkpointer)