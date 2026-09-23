import os
import sys
from dotenv import load_dotenv

# Add directory to sys.path to enable imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.llm_rotator import LLMRotator

def test_gateway():
    print("--------------------------------------------------")
    print("📡 Testing LLM Gateway connection from skill_for_digest...")
    
    # Load environment configuration
    load_dotenv(dotenv_path='.env.local')
    url = os.getenv("LLM_GATEWAY_URL")
    key = os.getenv("LLM_GATEWAY_KEY")
    
    print(f"Configured Gateway URL: {url}")
    print(f"Configured Gateway Key: {'[SET]' if key else '[NOT SET]'}")
    
    # Initialize rotator client
    rotator = LLMRotator()
    print(f"use_gateway setting detected: {rotator.use_gateway}")
    
    # Run test query
    messages = [{"role": "user", "content": "Say the word 'CONNECTION_TEST_PASSED' and nothing else."}]
    print("Sending message...")
    try:
        response = rotator.chat_completion(messages)
        print("--------------------------------------------------")
        print(f"Response: {response}")
        print("--------------------------------------------------")
        if "CONNECTION_TEST_PASSED" in response:
            print("🎉 SUCCESS: Connection to LLM Gateway is functional and correctly configured!")
        else:
            print("⚠️ WARNING: Received a response, but it did not contain the expected word.")
    except Exception as e:
        print("--------------------------------------------------")
        print(f"❌ ERROR: Failed to get response: {e}")
        print("--------------------------------------------------")

if __name__ == "__main__":
    test_gateway()
