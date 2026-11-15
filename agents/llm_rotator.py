import os
import json
import time
from openai import OpenAI
from dotenv import load_dotenv

class LLMRotator:
    def __init__(self):
        load_dotenv()
        load_dotenv(dotenv_path='.env.local', override=True)
        
        self.gateway_url = os.getenv("LLM_GATEWAY_URL", "http://localhost:8000/v1")
        self.gateway_key = os.getenv("LLM_GATEWAY_KEY")
        self.use_gateway = False
        
        # Try to ping the gateway's health endpoint to check availability
        import requests
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        try:
            base_url = self.gateway_url.rstrip('/')
            if base_url.endswith('/v1'):
                health_url = base_url[:-3] + '/health'
            else:
                health_url = base_url + '/health'
                
            response = requests.get(health_url, timeout=2.0, verify=False)
            if response.status_code == 200:
                health_data = response.json()
                if health_data.get("status") == "ok":
                    self.use_gateway = True
                    print(f"📡 [Rotator Client] Connected to LLM Gateway at {self.gateway_url}")
        except Exception:
            pass

        self.providers = [
            {
                "name": "cerebras_qwen",
                "base_url": "https://api.cerebras.ai/v1",
                "api_key": os.getenv("CEREBRAS_API_KEY"),
                "model": "qwen-3.8-27b"
            },
            {
                "name": "cerebras",
                "base_url": "https://api.cerebras.ai/v1",
                "api_key": os.getenv("CEREBRAS_API_KEY"),
                "model": "gpt-oss-120b"
            },
            {
                "name": "groq",
                "base_url": "https://api.groq.com/openai/v1",
                "api_key": os.getenv("GROQ_API_KEY"),
                "model": "meta-llama/llama-prompt-guard-2-22m"
            },
            {
                "name": "groq_86m",
                "base_url": "https://api.groq.com/openai/v1",
                "api_key": os.getenv("GROQ_API_KEY"),
                "model": "meta-llama/llama-prompt-guard-2-86m"
            },
            {
                "name": "sambanova",
                "base_url": "https://api.sambanova.ai/v1",
                "api_key": os.getenv("SAMBANOVA_API_KEY"),
                "model": "Meta-Llama-3.3-70B-Instruct"
            },
            {
                "name": "nvidia",
                "base_url": "https://integrate.api.nvidia.com/v1",
                "api_key": os.getenv("NVIDIA_API_KEY"),
                "model": "bigcode/starcoder2-15b"
            },
            {
                "name": "nvidia_glm",
                "base_url": "https://integrate.api.nvidia.com/v1",
                "api_key": os.getenv("NVIDIA_API_KEY"),
                "model": "z-ai/glm-5.3-flash",
                "extra_body": {"chat_template_kwargs": {"enable_thinking": True, "clear_thinking": False}}
            },
            {
                "name": "nvidia_guard",
                "base_url": "https://integrate.api.nvidia.com/v1",
                "api_key": os.getenv("NVIDIA_API_KEY"),
                "model": "nvidia/llama-3.1-nemotron-safety-guard-8b-v3"
            },
            {
                "name": "nvidia_mistral_nemotron",
                "base_url": "https://integrate.api.nvidia.com/v1",
                "api_key": os.getenv("NVIDIA_API_KEY"),
                "model": "mistralai/codestral-22b-instruct-v0.1"
            },
            {
                "name": "cloudflare",
                "base_url": f"https://api.cloudflare.com/client/v4/accounts/{os.getenv('CLOUDFLARE_ACCOUNT_ID')}/ai/v1",
                "api_key": os.getenv("CLOUDFLARE_API_KEY"),
                "model": "@cf/meta/llama-3.1-8b-instruct"
            },
            {
                "name": "openrouter",
                "base_url": "https://openrouter.ai/api/v1",
                "api_key": os.getenv("OPENROUTERFORSKILLFORDIGEST"),
                "model": "particle-ai/particle-1:free"
            },
            {
                "name": "ollama",
                "base_url": "http://localhost:11434/v1",
                "api_key": "ollama",
                "model": "qwen2.5-coder:14b"
            }
        ]
        
        if not self.use_gateway:
            print("⚠️ [Rotator Client] LLM Gateway is offline or not configured. Using local direct providers.")

        # Determine state path for daily checks
        agents_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(agents_dir)
        scratch_dir = os.path.join(project_root, "scratch")
        os.makedirs(scratch_dir, exist_ok=True)
        self.check_state_path = os.path.join(scratch_dir, "last_model_check.json")

        # Check and update provider models daily
        self._check_and_update_models_daily()

    def _save_active_model(self, model, provider, via_gateway):
        try:
            # Save to scratch/active_model.json
            scratch_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scratch")
            os.makedirs(scratch_dir, exist_ok=True)
            active_model_path = os.path.join(scratch_dir, "active_model.json")
            with open(active_model_path, "w", encoding="utf-8") as f:
                json.dump({
                    "model": model,
                    "provider": provider,
                    "via_gateway": via_gateway,
                    "timestamp": time.time()
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ Failed to save active model state: {e}")

    def chat_completion(self, messages, response_format=None, preferred_provider=None):
        """
        Attempts to get a chat completion from the LLM Gateway, or falls back to local providers.
        """
        if self.use_gateway:
            try:
                print(f"🤖 [Rotator Client] Routing request through gateway: {self.gateway_url}")
                import httpx
                http_client = httpx.Client(verify=False)
                client = OpenAI(
                    base_url=self.gateway_url,
                    api_key=self.gateway_key,
                    http_client=http_client
                )
                
                if not preferred_provider:
                    preferred_provider = os.getenv("PREFERRED_PROVIDER")
                
                params = {
                    "model": "auto",
                    "messages": messages,
                }
                if response_format:
                    params["response_format"] = response_format
                
                if preferred_provider and preferred_provider != "None":
                    params["extra_body"] = {"preferred_provider": preferred_provider}
                
                start_time = time.time()
                response = client.chat.completions.create(**params)
                duration = time.time() - start_time
                
                content = response.choices[0].message.content
                print(f"✅ [Rotator Client] Success via gateway ({response.model}) in {duration:.2f}s")
                self._save_active_model(response.model, preferred_provider or "auto", via_gateway=True)
                return content
            except Exception as e:
                print(f"⚠️ [Rotator Client] Gateway request failed: {e}. Falling back to direct providers...")

        # Direct provider rotation logic (original code)
        available_providers = [p for p in self.providers if p["api_key"] or p["name"] == "ollama"]
        
        if not available_providers:
            raise Exception("No LLM providers found.")

        # Reorder if a preferred provider is specified
        if not preferred_provider:
            preferred_provider = os.getenv("PREFERRED_PROVIDER")
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

                if "extra_body" in provider:
                    params["extra_body"] = provider["extra_body"]

                start_time = time.time()
                response = client.chat.completions.create(**params)
                duration = time.time() - start_time
                
                content = response.choices[0].message.content
                print(f"✅ [Rotator] Success via {provider['name']} in {duration:.2f}s")
                self._save_active_model(provider['model'], provider['name'], via_gateway=False)
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

    def _check_and_update_models_daily(self):
        try:
            now = time.time()
            needs_check = True
            if os.path.exists(self.check_state_path):
                with open(self.check_state_path, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                last_check = state.get("last_check", 0)
                if now - last_check < 86400: # 24 hours
                    needs_check = False
            
            if needs_check:
                print("🔄 [Rotator] Starting daily check of AI models availability...")
                self._update_provider_models()
                with open(self.check_state_path, 'w', encoding='utf-8') as f:
                    json.dump({"last_check": now}, f)
                print("✅ [Rotator] Daily model check complete.")
        except Exception as e:
            print(f"⚠️ [Rotator] Error during daily model check: {e}")

    def _update_provider_models(self):
        import requests
        import re
        
        file_path = __file__
        if not os.path.exists(file_path):
            return
            
        with open(file_path, 'r', encoding='utf-8') as f:
            file_content = f.read()
            
        modified = False
        
        for provider in self.providers:
            if provider["name"] == "ollama" or not provider["api_key"]:
                continue
                
            try:
                headers = {"Authorization": f"Bearer {provider['api_key']}"}
                if provider["name"] == "cloudflare":
                    # Cloudflare endpoint handles standard models differently
                    continue
                    
                response = requests.get(f"{provider['base_url']}/models", headers=headers, timeout=5.0)
                if response.status_code != 200:
                    continue
                    
                data = response.json()
                available_models = [m["id"] for m in data.get("data", [])]
                if not available_models:
                    continue
                    
                current_model = provider["model"]
                if current_model in available_models:
                    continue
                    
                new_model = self._select_best_replacement(current_model, available_models)
                if new_model and new_model != current_model:
                    print(f"🔄 [Rotator] Model '{current_model}' for '{provider['name']}' is no longer available. Replacing with '{new_model}'.")
                    provider["model"] = new_model
                    
                    pattern = r'(["\']name["\']:\s*["\']' + re.escape(provider["name"]) + r'["\'],[^}]+?["\']model["\']:\s*["\'])[^"\']+?(["\'])'
                    file_content, count = re.subn(pattern, rf'\g<1>{new_model}\g<2>', file_content, flags=re.DOTALL)
                    if count > 0:
                        modified = True
            except Exception as e:
                print(f"⚠️ [Rotator] Failed to check models for '{provider['name']}': {e}")
                
        if modified:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(file_content)
                print("💾 [Rotator] Configuration file llm_rotator.py updated with new models.")
            except Exception as e:
                print(f"⚠️ [Rotator] Failed to write updated config to file: {e}")

    def _select_best_replacement(self, current_model, available_models):
        import re
        for m in available_models:
            if m.lower() == current_model.lower():
                return m
                
        tokens = re.split(r'[-_/\s.]', current_model.lower())
        keywords = [t for t in tokens if len(t) > 1 and t not in ['api', 'v1', 'openai', 'instruct', 'versatile', 'free']]
        
        best_model = None
        best_score = -1
        
        for m in available_models:
            m_lower = m.lower()
            if any(term in m_lower for term in ['deprecated', 'test', 'preview', 'dev']):
                continue
                
            score = 0
            for kw in keywords:
                if kw in m_lower:
                    score += len(kw)
            for arch in ['llama', 'qwen', 'glm', 'claude', 'gpt']:
                if arch in current_model.lower() and arch in m_lower:
                    score += 10
            if score > best_score:
                best_score = score
                best_model = m
                
        return best_model or (available_models[0] if available_models else None)

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    rotator = LLMRotator()
    try:
        res = rotator.chat_completion([{"role": "user", "content": "Say 'Hello'"}])
        print(f"Result: {res}")
    except Exception as e:
        print(f"Final Error: {e}")
