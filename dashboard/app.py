import streamlit as st
import os
import sys
import time
import json
import subprocess
import signal
import pandas as pd
from minio import Minio

# Add root directory to sys.path to enable imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set page configurations
st.set_page_config(
    page_title="Legal AI Agent Dashboard",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load CSS Styles
styles_path = os.path.join(os.path.dirname(__file__), 'styles.css')
if os.path.exists(styles_path):
    with open(styles_path, 'r', encoding='utf-8') as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Initialize Storage & Rotator
minio_available = False
minio_error = None
storage = None

try:
    from tools.storage_tools import MinioStorage
    storage = MinioStorage()
    minio_available = True
except Exception as e:
    minio_error = str(e)

try:
    from agents.llm_rotator import LLMRotator
    rotator = LLMRotator()
    rotator_available = True
except Exception as e:
    rotator = None
    rotator_available = False

# Helper functions
def is_process_running(pid):
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False

def get_missing_queue():
    missing_list_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'agents', 'lists', 'list_of_missing_structured.md')
    queue = []
    if os.path.exists(missing_list_path):
        with open(missing_list_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith("- "):
                    queue.append(line[2:])
    return queue

def get_processed_documents():
    slugs = set()
    local_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "documents", "structured")
    if os.path.exists(local_dir):
        for entry in os.listdir(local_dir):
            if os.path.isdir(os.path.join(local_dir, entry)):
                slugs.add(entry)
    
    if minio_available and storage:
        try:
            minio_slugs = storage.get_processed_slugs()
            slugs.update(minio_slugs)
        except Exception as e:
            st.sidebar.warning(f"⚠️ Не вдалося оновити slugs з MinIO: {e}")
            
    return sorted(list(slugs))

def get_articles_for_document(doc_slug):
    articles = {}
    local_doc_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "documents", "structured", doc_slug)
    
    if os.path.exists(local_doc_dir):
        for entry in os.listdir(local_doc_dir):
            if entry.endswith(".json"):
                article_id = entry[:-5]
                local_path = os.path.join(local_doc_dir, entry)
                try:
                    with open(local_path, "r", encoding="utf-8") as f:
                        articles[article_id] = json.load(f)
                except:
                    pass
                    
    if minio_available and storage:
        try:
            minio_jsons = storage.client.list_objects(storage.bucket_name, prefix=f"structured/{doc_slug}/", recursive=True)
            for obj in minio_jsons:
                art_id = os.path.basename(obj.object_name)
                if art_id.endswith(".json"):
                    art_id_key = art_id[:-5]
                    if art_id_key not in articles:
                        import tempfile
                        tmp_path = None
                        try:
                            with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
                                tmp_path = tmp.name
                                storage.client.fget_object(storage.bucket_name, obj.object_name, tmp_path)
                            with open(tmp_path, "r", encoding="utf-8") as f:
                                articles[art_id_key] = json.load(f)
                        except:
                            pass
                        finally:
                            if tmp_path and os.path.exists(tmp_path):
                                os.remove(tmp_path)
        except:
            pass
            
    return articles

def test_provider_connectivity(provider):
    import openai
    if not provider["api_key"] and provider["name"] != "ollama":
        return "Missing API Key"
    try:
        client = openai.OpenAI(
            base_url=provider["base_url"],
            api_key=provider["api_key"] if provider["api_key"] else "ollama"
        )
        start_time = time.time()
        client.chat.completions.create(
            model=provider["model"],
            messages=[{"role": "user", "content": "Say 'OK'"}],
            max_tokens=5,
            timeout=5.0
        )
        duration = time.time() - start_time
        return f"🟢 Active ({duration:.2f}s)"
    except Exception as e:
        return f"🔴 Error: {str(e)[:50]}..."

# Sidebar
st.sidebar.markdown("### ⚖️ Legal AI Agent")
st.sidebar.caption("Панель керування та моніторингу")
st.sidebar.markdown("---")

# Storage Info in Sidebar
st.sidebar.markdown("#### 📦 Стан сховища MinIO")
if minio_available:
    st.sidebar.markdown(f"<span class='status-pill status-pill-green'>🟢 MinIO Connected</span>", unsafe_allow_html=True)
    st.sidebar.caption(f"Bucket: `{storage.bucket_name}`")
    st.sidebar.caption(f"Endpoint: `{storage.endpoint}`")
else:
    st.sidebar.markdown(f"<span class='status-pill status-pill-red'>🔴 MinIO Offline</span>", unsafe_allow_html=True)
    st.sidebar.error(f"Помилка підключення:\n{minio_error}")

st.sidebar.markdown("---")

# Provider override in Sidebar
st.sidebar.markdown("#### 🤖 LLM Провайдери")
if rotator_available and rotator:
    # Set default preferred provider in session state
    if "preferred_provider" not in st.session_state:
        st.session_state.preferred_provider = os.getenv("PREFERRED_PROVIDER", "None")

    provider_names = ["None"] + [p["name"] for p in rotator.providers]
    selected_prov = st.sidebar.selectbox(
        "Пріоритетний LLM провайдер",
        options=provider_names,
        index=provider_names.index(st.session_state.preferred_provider) if st.session_state.preferred_provider in provider_names else 0,
        help="Цей провайдер буде спробований першим при запуску агента."
    )
    
    if selected_prov != st.session_state.preferred_provider:
        st.session_state.preferred_provider = selected_prov
        st.sidebar.toast(f"Пріоритет змінено на: {selected_prov}")

    # Provider testing panel
    if st.sidebar.button("🔍 Тест швидкодії провайдерів", width='stretch'):
        st.sidebar.markdown("**Статус підключення:**")
        for prov in rotator.providers:
            with st.spinner(f"Тестуємо {prov['name']}..."):
                status = test_provider_connectivity(prov)
                st.sidebar.caption(f"**{prov['name'].upper()}**: {status}")
else:
    st.sidebar.error("Провайдери LLM недоступні.")

st.sidebar.markdown("---")
st.sidebar.caption("© 2026 Legal AI Segmenter")

# Main Page Header
st.markdown("<h1 class='main-title'>⚖️ Аналітична Панель AI-Агента</h1>", unsafe_allow_html=True)
st.markdown("Платформа для обробки, структурування та аналізу судових рішень і дайджестів.")

# Fetch statistics
total_pdfs = 0
total_structured = 0
queue_size = 0
missing_queue_list = []

if minio_available and storage:
    try:
        # Fetching statistics from MinIO
        with st.spinner("Оновлення метрик..."):
            md_files = storage.list_markdown_files()
            processed_slugs = storage.get_processed_slugs()
            
            # Queue size (PDFs pending markdown conversion or Markdown files pending structure JSON)
            missing_queue_list = get_missing_queue()
            queue_size = len(missing_queue_list)
            
            # Count PDFs
            pdf_objs = storage.client.list_objects(storage.bucket_name, prefix='pdfs/', recursive=True)
            total_pdfs = len([obj for obj in pdf_objs if obj.object_name.lower().endswith('.pdf')])
            
            total_structured = len(processed_slugs)
    except Exception as e:
        st.warning(f"Помилка при оновленні статистики сховища: {e}")

# Metric Cards Row
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric(label="Всього PDF у MinIO", value=f"{total_pdfs} файлів", delta=None)
with col2:
    st.metric(label="Оброблено (Structured)", value=f"{total_structured} slugs", delta=None)
with col3:
    st.metric(label="Залишилось у черзі", value=f"{queue_size} файлів", delta=f"{queue_size} на обробку", delta_color="inverse")
with col4:
    # Determine the actual model name dynamically
    display_value = "Невідомо"
    delta_val = "Не визначено"
    gateway_status = "⚠️ Немає інформації про гейтвей"
    
    if rotator_available and rotator:
        pref = st.session_state.get("preferred_provider", "None")
        
        # Read from active_model.json if it exists
        active_model_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scratch", "active_model.json")
        last_used = None
        if os.path.exists(active_model_path):
            try:
                with open(active_model_path, "r", encoding="utf-8") as f:
                    last_used = json.load(f)
            except:
                pass
        
        # If the gateway is online
        if rotator.use_gateway:
            gateway_status = f"🟢 Connected to LLM Gateway at {rotator.gateway_url}"
            if pref != "None":
                # Find matching provider model
                model_name = next((p["model"] for p in rotator.providers if p["name"] == pref), f"Gateway ({pref})")
                display_value = model_name
                delta_val = f"Priority: {pref.upper()} (via Gateway)"
            else:
                # Gateway Auto
                if last_used and last_used.get("via_gateway") and last_used.get("model"):
                    display_value = last_used["model"]
                else:
                    display_value = "Gateway Auto"
                delta_val = "Gateway Auto-routing"
        else:
            # Gateway is offline - using direct providers
            gateway_status = "🔴 LLM Gateway is offline. Using direct providers."
            actual_provider = pref
            if not actual_provider or actual_provider == "None":
                # Fallback to the first available provider in the list
                available = [p for p in rotator.providers if p["api_key"] or p["name"] == "ollama"]
                actual_provider = available[0]["name"] if available else "None"
                
            model_name = next((p["model"] for p in rotator.providers if p["name"] == actual_provider), "No LLM Available")
            display_value = model_name
            delta_val = f"Direct: {actual_provider.upper()} (Fallback)" if pref == "None" else f"Direct: {actual_provider.upper()}"
            
        # Check if the active_model.json was updated recently (e.g. during a running agent job in the last 10 minutes)
        if last_used and time.time() - last_used.get("timestamp", 0) < 600:
            display_value = last_used["model"]
            delta_val = f"Last Used: {last_used['provider'].upper()}"
            
        st.metric(label="Активний LLM", value=display_value, delta=delta_val, help=gateway_status)
    else:
        st.metric(label="Активний LLM", value=display_value, delta=delta_val, help=gateway_status)

st.markdown("---")

# Main tabs
tab1, tab2 = st.tabs(["🚀 Моніторинг та Запуск", "📋 Провідник Документів"])

with tab1:
    col_left, col_right = st.columns([3, 2])
    
    with col_left:
        st.subheader("🚀 Керування фоновим конвеєром")
        
        # Check process status
        if "process_active" not in st.session_state:
            st.session_state.process_active = False
            st.session_state.process_pid = None
            st.session_state.process_start_time = None

        # Verify if process is still running actually
        if st.session_state.process_active and st.session_state.process_pid:
            if not is_process_running(st.session_state.process_pid):
                st.session_state.process_active = False
                st.session_state.process_pid = None
        
        # Target file options
        target_options = ["Вся черга (All)"] + missing_queue_list
        target_selection = st.selectbox(
            "Оберіть файл для обробки",
            options=target_options,
            disabled=st.session_state.process_active,
            help="Ви можете обрати запуск обробки всієї черги або окремого конкретного файлу."
        )
        
        # Run / Stop buttons
        btn_col1, btn_col2 = st.columns(2)
        
        with btn_col1:
            if st.button("🚀 Запустити обробку черги", width='stretch', type="primary", disabled=st.session_state.process_active):
                log_file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scratch", "agent_run.log")
                os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
                
                with open(log_file_path, "w", encoding="utf-8") as f:
                    f.write(f"=== [СТАРТ СЕСІЇ АГЕНТА: {time.strftime('%Y-%m-%d %H:%M:%S')}] ===\n")
                    f.write(f"Ціль: {target_selection}\n")
                    f.write(f"Пріоритетний LLM: {st.session_state.preferred_provider}\n")
                    f.write(f"----------------------------------------\n\n")

                cmd = [sys.executable, "run_agent.py"]
                if target_selection != "Вся черга (All)":
                    cmd.append(target_selection)

                # Setup Env with preferred provider
                env = os.environ.copy()
                if st.session_state.preferred_provider != "None":
                    env["PREFERRED_PROVIDER"] = st.session_state.preferred_provider

                # Spawn subprocess
                log_file = open(log_file_path, "a", encoding="utf-8")
                p = subprocess.Popen(
                    cmd,
                    cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    env=env,
                    text=True
                )
                
                st.session_state.process_pid = p.pid
                st.session_state.process_active = True
                st.session_state.process_start_time = time.time()
                st.rerun()
                
        with btn_col2:
            if st.button("🛑 Зупинити процес", width='stretch', type="secondary", disabled=not st.session_state.process_active):
                if st.session_state.process_pid:
                    try:
                        os.kill(st.session_state.process_pid, signal.SIGTERM)
                        time.sleep(1.0)
                        if is_process_running(st.session_state.process_pid):
                            os.kill(st.session_state.process_pid, signal.SIGKILL)
                        
                        log_file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scratch", "agent_run.log")
                        with open(log_file_path, "a", encoding="utf-8") as f:
                            f.write("\n🛑 Процес примусово зупинено користувачем.\n")
                    except Exception as e:
                        st.error(f"Помилка зупинки: {e}")
                    
                    st.session_state.process_active = False
                    st.session_state.process_pid = None
                    st.rerun()

        # Real-time console logs rendering
        log_file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scratch", "agent_run.log")
        if os.path.exists(log_file_path):
            with open(log_file_path, "r", encoding="utf-8") as f:
                logs = f.read()
            
            with st.expander("📝 Лог виконання (в реальному часі)", expanded=st.session_state.process_active):
                st.code(logs, language="bash")
        
        # Periodic auto-reload during active runs
        if st.session_state.process_active:
            st.caption("⏳ Агент працює... Вікно логів оновлюється автоматично кожні 1.5 сек.")
            time.sleep(1.5)
            st.rerun()
            
    with col_right:
        st.subheader("📋 Стан черги обробки")
        if queue_size > 0:
            st.warning(f"Знайдено {queue_size} файлів у черзі на структурування")
            # Create a simple DataFrame for styling
            queue_df = pd.DataFrame(missing_queue_list, columns=["Назва файлу (Slug)"])
            st.dataframe(queue_df, width='stretch', height=400)
        else:
            st.success("🎉 Черга порожня! Всі файли успішно структуровано та оброблено.")

with tab2:
    st.subheader("🔍 Перегляд та редагування структурованих документів")
    
    processed_slugs = get_processed_documents()
    
    if processed_slugs:
        # Split layout for document selection and file selection
        doc_col1, doc_col2 = st.columns(2)
        with doc_col1:
            selected_doc = st.selectbox("Оберіть структурований документ (slug)", processed_slugs)
            
        articles = get_articles_for_document(selected_doc)
        
        if articles:
            with doc_col2:
                selected_art_id = st.selectbox("Оберіть статтю/розділ", sorted(list(articles.keys())))
                
            selected_article = articles[selected_art_id]
            
            st.markdown("---")
            
            # Form to edit fields
            st.markdown("### 📝 Редагування структурованих даних")
            
            # Read values from JSON
            val_teza = selected_article.get("teza", "")
            val_case = selected_article.get("case_number", "")
            val_date = selected_article.get("date", "")
            val_cat = selected_article.get("category", "")
            val_summary = selected_article.get("summary", "")
            val_circumstances = selected_article.get("circumstances", "")
            val_reasoning = selected_article.get("reasoning", "")
            val_url = selected_article.get("url", "")
            
            # Extracted from nested metadata
            metadata = selected_article.get("metadata", {})
            val_court = metadata.get("court", selected_article.get("court", ""))
            val_source = metadata.get("source_digest", selected_article.get("source_digest", ""))
            
            # Show markdown content and editor side-by-side
            view_col1, view_col2 = st.columns([1, 1])
            
            with view_col1:
                st.markdown("#### 📄 Оригінальний текст (Markdown)")
                orig_markdown = selected_article.get("full_markdown", "")
                if orig_markdown:
                    st.markdown(f"<div style='border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; padding: 15px; background: rgba(255,255,255,0.02); height: 750px; overflow-y: auto;'>{orig_markdown}</div>", unsafe_allow_html=True)
                else:
                    st.info("Текст Markdown відсутній у структурованому JSON.")
                    
            with view_col2:
                st.markdown("#### ✏️ Поля структурованого JSON")
                
                with st.form("edit_article_form"):
                    st.markdown("##### 📁 Ідентифікатори справи")
                    col_info1, col_info2, col_info3 = st.columns(3)
                    with col_info1:
                        new_case = st.text_input("Номер справи (case_number)", value=val_case)
                    with col_info2:
                        new_date = st.text_input("Дата рішення (date)", value=val_date)
                    with col_info3:
                        new_court = st.text_input("Суд (court)", value=val_court)
                        
                    col_info4, col_info5, col_info6 = st.columns(3)
                    with col_info4:
                        new_cat = st.text_input("Категорія (category)", value=val_cat)
                    with col_info5:
                        new_url = st.text_input("URL рішення (url)", value=val_url)
                    with col_info6:
                        new_source = st.text_input("Джерело (source_digest)", value=val_source)
                        
                    st.markdown("##### 📝 Зміст та правові позиції")
                    new_teza = st.text_area("Правова теза (teza)", value=val_teza, height=80)
                    new_summary = st.text_area("Короткий опис (summary)", value=val_summary, height=80)
                    new_circumstances = st.text_area("Обставини справи (circumstances)", value=val_circumstances, height=80)
                    new_reasoning = st.text_area("Правовий висновок (reasoning)", value=val_reasoning, height=80)
                    
                    submit_button = st.form_submit_button("💾 Зберегти зміни", width='stretch')
                    
                if submit_button:
                    # Update data preserving other fields
                    updated_data = selected_article.copy()
                    updated_data.update({
                        "teza": new_teza,
                        "case_number": new_case,
                        "date": new_date,
                        "category": new_cat,
                        "summary": new_summary,
                        "circumstances": new_circumstances,
                        "reasoning": new_reasoning,
                        "url": new_url
                    })
                    
                    # Update nested metadata structure
                    if "metadata" not in updated_data or not isinstance(updated_data["metadata"], dict):
                        updated_data["metadata"] = {}
                    
                    updated_data["metadata"]["court"] = new_court
                    updated_data["metadata"]["source_digest"] = new_source
                    
                    # Clean up old top-level duplicates if any
                    if "court" in updated_data:
                        del updated_data["court"]
                    if "source_digest" in updated_data:
                        del updated_data["source_digest"]
                    
                    # Save local file
                    local_doc_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "documents", "structured", selected_doc)
                    os.makedirs(local_doc_dir, exist_ok=True)
                    local_path = os.path.join(local_doc_dir, f"{selected_art_id}.json")
                    
                    with open(local_path, "w", encoding="utf-8") as f:
                        json.dump(updated_data, f, ensure_ascii=False, indent=2)
                        
                    # Save to MinIO
                    if minio_available and storage:
                        try:
                            target_minio_path = f"structured/{selected_doc}/{selected_art_id}.json"
                            storage.client.fput_object(storage.bucket_name, target_minio_path, local_path, content_type='application/json')
                            st.success("✅ Зміни успішно збережено локально та синхронізовано з MinIO!")
                            st.toast("Збережено!")
                            # Refresh state
                            st.rerun()
                        except Exception as e:
                            st.error(f"Помилка завантаження в MinIO: {e}")
                    else:
                        st.success("✅ Зміни успішно збережено локально (MinIO недоступний)!")
                        st.toast("Збережено локально!")
                        st.rerun()

                st.markdown(" ")
                st.download_button(
                    label="📥 Скачати JSON файл",
                    data=json.dumps(selected_article, ensure_ascii=False, indent=2),
                    file_name=f"{selected_art_id}.json",
                    mime="application/json",
                    width='stretch'
                )
            
            st.markdown("---")
            # Raw JSON view
            with st.expander("👁️ Переглянути сирий JSON"):
                st.json(selected_article)
        else:
            st.info(f"Для документа `{selected_doc}` ще немає структурованих JSON-файлів.")
    else:
        st.info("Не знайдено жодного структурованого документа в системі.")
