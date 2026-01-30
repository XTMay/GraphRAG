
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

try:
    from src.agent import SmartHomeAgent
    
    print("Initializing agent...")
    agent = SmartHomeAgent(debug=True)
    
    request = "Make the living room cozy for movie night"
    print(f"Running request: {request}")
    
    response, trace = agent.run_with_trace(request)
    
    print(f"Response: {response}")
    print(f"Trace type: {type(trace)}")
    print(f"Trace value: {trace}")
    
    if trace is None:
        print("ERROR: Trace is None!")
    else:
        print("Trace is iterable.")
        for i, step in enumerate(trace, 1):
            print(f"{i}. {step}")
            
except Exception as e:
    print(f"Exception occurred: {e}")
    import traceback
    traceback.print_exc()
