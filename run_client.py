import sys
from src.client.graph_client import build_and_execute_workflow
from src.config.settings import logger

if __name__ == "__main__":
    prompt = "Plan a 3-day trip to Tokyo, check the weather there, and email the final plan to sakthivelsanthosh069@gmail.com."
    
    if len(sys.argv) > 1:
        prompt = " ".join(sys.argv[1:])
        
    try:
        final_output = build_and_execute_workflow(user_prompt=prompt)
        print("\n" + "="*50)
        print("FINAL WORKFLOW OUTPUT:")
        print("="*50)
        print(final_output)
    except Exception as e:
        logger.critical(f"Workflow execution failed: {e}")