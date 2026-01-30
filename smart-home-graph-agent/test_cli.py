
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    from src.agent import SmartHomeAgent
    
    print("Initializing agent...")
    agent = SmartHomeAgent(debug=True)
    
    request = "Turn on the kitchen lights"
    print(f"Running request: {request}")
    
    response, trace = agent.run_with_trace(request)
    
    print(f"Response: {response}")
    if trace:
        print("Trace steps:")
        for i, step in enumerate(trace, 1):
            print(f"{i}. {step}")
    else:
        print("No trace available.")
            
except Exception as e:
    print(f"Exception occurred: {e}")
    import traceback
    traceback.print_exc()
