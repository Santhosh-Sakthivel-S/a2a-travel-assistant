import streamlit as st
import os

from src.config.settings import settings
from src.tools.weather import fetch_weather
from src.tools.email_tool import send_email
from strands import Agent, tool
from strands.agent.a2a_agent import A2AAgent

# Import database functions
from src.database.db import (
    init_db, create_session, get_all_sessions, 
    get_messages_for_session, add_message, update_session_title
)

# Set AWS Region
os.environ["AWS_DEFAULT_REGION"] = settings.AWS_REGION

st.set_page_config(page_title="Travel & Weather Assistant", page_icon="✈️")

# Initialize Database on first run
@st.cache_resource
def setup_database():
    init_db()

setup_database()

# --- 1. Wrapped Tool ---
@tool
def plan_trip(destination: str, weather_context: str, days: int) -> str:
    """
    Use this tool to generate a detailed travel itinerary.
    You MUST provide the 'destination', 'weather_context', and the number of 'days'.
    """
    try:
        remote_planner = A2AAgent(endpoint="http://localhost:8000", name="remote_trip_planner")
        prompt = (
            f"Please plan a {days}-day trip to {destination}. Consider this weather: {weather_context}.\n\n"
            f"CRITICAL FORMATTING RULES - FOLLOW THESE EXACTLY:\n"
            f"1. DO NOT use time-of-day breakdowns like 'Morning', 'Afternoon', or 'Evening'.\n"
            f"2. For each day, provide a list of EXACTLY 5 specific places to visit.\n"
            f"3. Number the spots 1 through 5 for each day.\n"
            f"4. ONLY OUTPUT THE NAME OF THE PLACE. DO NOT include descriptions. Just the name."
        )
        result = remote_planner(prompt)
        raw_msg = result.message
        if isinstance(raw_msg, dict) and 'content' in raw_msg:
            return raw_msg['content'][0]['text']
        elif isinstance(raw_msg, list) and len(raw_msg) > 0 and 'text' in raw_msg[0]:
            return raw_msg[0]['text']
        elif isinstance(raw_msg, str):
            return raw_msg
        return str(raw_msg)
    except Exception as e:
        return f"Failed to contact remote trip planner: {str(e)}"

# --- 2. Initialize Agent ---
if "orchestrator" not in st.session_state:
    st.session_state.orchestrator = Agent(
        name="ChatBot",
        model=settings.BEDROCK_MODEL_ID,
        system_prompt=(
            "You are a strict, direct execution travel assistant. DO NOT use conversational filler when executing tasks.\n\n"
            "Follow these strict execution steps based on the user's INTENT:\n"
            "1. GREETINGS: If the user sends a greeting like 'hi', 'hii', or 'hello', you MUST reply EXACTLY with the phrase: 'AI Travel & Weather Assistant how can i assist today'. Do not add any other words.\n"
            "2. TRIP PLANNING INTENT: If the user specifically asks to plan a trip, analyze their prompt for the Destination and the Number of Days.\n"
            "3. MISSING DAYS: If they provided a Destination but NO Number of Days, ask ONLY: 'how many days you plan to stay there.'\n"
            "4. MISSING DESTINATION: If they provided the Number of Days but NO Destination, ask ONLY: 'Which place would you like to visit?'\n"
            "5. EXECUTION: Once you have BOTH the Destination and the Number of Days, execute the 'fetch_weather' tool.\n"
            "6. Execute the 'plan_trip' tool using the destination, days, and the fetched weather.\n"
            "7. Output the exact itinerary as the 'plan_trip' tool returns it. Do not add any introductory or concluding remarks.\n"
            "8. If the user asks for an email, execute the 'send_email' tool."
        ),
        tools=[fetch_weather, send_email, plan_trip] 
    )

# --- 3. Session Management UI (Sidebar) ---
with st.sidebar:
    st.header("🗂️ Chat History")
    
    # Add New Chat Button
    if st.button("➕ New Chat", use_container_width=True):
        new_session_id = create_session("New Chat")
        st.session_state.current_session_id = new_session_id
        
        # Add initial greeting to DB
        greeting = "AI Travel & Weather Assistant how can i assist today"
        add_message(new_session_id, "assistant", greeting)
        
        # Clear agent memory
        if "orchestrator" in st.session_state:
            del st.session_state["orchestrator"]
            
        st.rerun()

    st.divider()
    
    # Load and display past sessions from DB
    sessions = get_all_sessions()
    for session in sessions:
        # Highlight the active session
        is_active = session['id'] == st.session_state.get('current_session_id')
        btn_label = f"{'👉 ' if is_active else ''}{session['title']} ({session['created_at'].strftime('%b %d')})"
        
        if st.button(btn_label, key=f"session_{session['id']}", use_container_width=True):
            st.session_state.current_session_id = session['id']
            # Clear agent memory when switching sessions so it forgets the previous chat
            if "orchestrator" in st.session_state:
                del st.session_state["orchestrator"]
            st.rerun()

# --- 4. Load Current Session ---
# Ensure a session exists on first load
if "current_session_id" not in st.session_state:
    sessions = get_all_sessions()
    if sessions:
        st.session_state.current_session_id = sessions[0]['id']
    else:
        new_id = create_session("New Chat")
        st.session_state.current_session_id = new_id
        add_message(new_id, "assistant", "AI Travel & Weather Assistant how can i assist today")

# Load messages for the active session from Postgres
active_session_id = st.session_state.current_session_id
db_messages = get_messages_for_session(active_session_id)
st.session_state.messages = db_messages

st.title("✈️ AI Travel & Weather Assistant")

# Display Conversation
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- 5. Chat Input & Execution ---
if user_prompt := st.chat_input("E.g., Plan a 4-day trip to Kodaikanal"):
    
    # Update title if it's the first user message
    if len(st.session_state.messages) <= 1:
        # Truncate prompt for a clean title
        new_title = user_prompt[:30] + "..." if len(user_prompt) > 30 else user_prompt
        update_session_title(active_session_id, new_title)

    # 1. Save user prompt to DB and UI
    add_message(active_session_id, "user", user_prompt)
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    
    with st.chat_message("user"):
        st.markdown(user_prompt)

    # 2. Generate Assistant Response
    with st.chat_message("assistant"):
        with st.spinner("Executing tools..."):
            try:
                # To maintain context, we need to feed the historical DB messages into the newly initialized Strands agent 
                # if we just switched to an older chat. The agent handles context automatically during active chatting.
                response = st.session_state.orchestrator(user_prompt)
                raw_reply = response.message
                
                bot_reply = ""
                if isinstance(raw_reply, dict) and 'content' in raw_reply:
                    content_list = raw_reply['content']
                    if isinstance(content_list, list) and len(content_list) > 0 and 'text' in content_list[0]:
                        bot_reply = content_list[0]['text']
                    else:
                        bot_reply = str(raw_reply)
                elif isinstance(raw_reply, list) and len(raw_reply) > 0 and 'text' in raw_reply[0]:
                    bot_reply = raw_reply[0]['text']
                elif isinstance(raw_reply, str):
                    bot_reply = raw_reply
                else:
                    bot_reply = str(raw_reply)
                
                st.markdown(bot_reply)
                
                # Save assistant reply to DB and UI
                add_message(active_session_id, "assistant", bot_reply)
                st.session_state.messages.append({"role": "assistant", "content": bot_reply})
                
                # Refresh UI to update the title in the sidebar
                if len(st.session_state.messages) <= 3:
                    st.rerun()
                
            except Exception as e:
                error_msg = f"An error occurred: {str(e)}"
                st.error(error_msg)
                add_message(active_session_id, "assistant", error_msg)
                st.session_state.messages.append({"role": "assistant", "content": error_msg})