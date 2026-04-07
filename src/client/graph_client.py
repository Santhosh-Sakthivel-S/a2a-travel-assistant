import strands
from strands import Agent
from strands.agent.a2a_agent import A2AAgent
from strands.multiagent.graph import GraphBuilder
from src.tools.weather import fetch_weather
from src.tools.email_tool import send_email
from src.config.settings import logger

def build_and_execute_workflow(user_prompt: str, server_url: str = "http://localhost:8000"):
    """Builds the deterministic graph and executes the user request."""

    weather_agent = Agent(
        name="weather_gatherer",
        system_prompt=(
            "Extract the requested destination from the user's prompt. "
            "Use the fetch_weather tool to get the weather. "
            "Output the destination and the exact weather data."
        ),
        tools=[fetch_weather]
    )


    trip_planner_node = A2AAgent(
        endpoint=server_url,
        name="remote_trip_planner",
        timeout=120 
    )

    email_agent = Agent(
        name="email_communicator",
        system_prompt=(
            "You will receive a complete travel itinerary from the previous step. "
            "Extract the target email address from the initial user request. "
            "Use the send_email tool to send the itinerary to that address. "
            "Return a final confirmation message."
        ),
        tools=[send_email]
    )

    builder = GraphBuilder()
    builder.add_node(weather_agent, "gather_weather")
    builder.add_node(trip_planner_node, "plan_trip")
    builder.add_node(email_agent, "send_email")

    builder.add_edge("gather_weather", "plan_trip")
    builder.add_edge("plan_trip", "send_email")

    graph = builder.build()

    logger.info(f"Executing Workflow. Prompt: '{user_prompt}'")
    result = graph(user_prompt)
    return result.message