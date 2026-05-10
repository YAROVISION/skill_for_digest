import os
import json
import time
from openai import OpenAI

class LLMRotator:
    def __init__(self):
        self.providers = [
            {
                "name": "groq",
                "base_url": "https://api.groq.com/openai/v1",
                "api_key": os.getenv("GROQ_API_KEY"),
                "model": "llama-3.3-70b-versatile"
            },
            {
                "name": "cerebras",
                "base_url": "https://api.cerebras.ai/v1",
                "api_key": os.getenv("CEREBRAS_API_KEY"),
                "model": "llama-3.3-70b"
            },
            {
                "name": "sambanova",
                "base_url": "https://api.sambanova.ai/v1",
                "api_key": os.getenv("SAMBANOVA_API_KEY"),
                "model": "Meta-Llama-3.3-70B-Instruct"
            },
            {
                "name": "ollama",
                "base_url": "http://localhost:11434/v1",
                "api_key": "ollama",
                "model": "qwen2.5-coder:14b"
            }
        ]
        
    def chat_completion(self, messages, response_format=None, preferred_provider=None):
        """
        Attempts to get a chat completion from providers in order.
        """
        # Filter out providers without API keys (except ollama)
        available_providers = [p for p in self.providers if p["api_key"] or p["name"] == "ollama"]
        
        if not available_providers:
            raise Exception("No LLM providers found.")

        # Reorder if a preferred provider is specified
        if preferred_provider:
            available_providers.sort(key=lambda x: x["name"] != preferred_provider)

        last_exception = None
        for provider in available_providers:
            try:
                print(f"🤖 [Rotator] Trying provider: {provider['name']} ({provider['model']})")
                client = OpenAI(
                    base_url=provider["base_url"],
                    api_key=provider["api_key"]
                )
                
                params = {
                    "model": provider["model"],
                    "messages": messages,
                }
                
                if response_format:
                    params["response_format"] = response_format

                start_time = time.time()
                response = client.chat.completions.create(**params)
                duration = time.time() - start_time
                
                content = response.choices[0].message.content
                print(f"✅ [Rotator] Success via {provider['name']} in {duration:.2f}s")
                return content

            except Exception as e:
                error_msg = str(e).lower()
                print(f"⚠️ [Rotator] Error with {provider['name']}: {e}")
                
                # Check for rate limit or specific errors that warrant a fallback
                if "rate limit" in error_msg or "429" in error_msg or "too many requests" in error_msg:
                    print(f"🔄 [Rotator] Rate limit hit for {provider['name']}. Falling back...")
                    last_exception = e
                    continue
                else:
                    last_exception = e
                    continue

        print("❌ [Rotator] All providers failed.")
        if last_exception:
            raise last_exception
        else:
            raise Exception("All LLM providers failed.")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    rotator = LLMRotator()
    try:
        res = rotator.chat_completion([{"role": "user", "content": "Say 'Hello'"}])
        print(f"Result: {res}")
    except Exception as e:
        print(f"Final Error: {e}")
