import html
import os
import subprocess
import sys
import time
import urllib.parse
import streamlit as st

# Add root directory to sys.path to enable imports
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT_DIR)

LOCAL_PDFS_DIR = os.path.join(ROOT_DIR, "agents", "pdfs")
LOCAL_MARKDOWN_DIR = os.path.join(ROOT_DIR, "agents", "markdown")

# Set page configurations
st.set_page_config(
    page_title="Legal PDF & Markdown Manager",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Load QuickLiquid CSS Styles
styles_path = os.path.join(os.path.dirname(__file__), "styles.css")
if os.path.exists(styles_path):
    with open(styles_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# QuickLiquid Ambient Goo Background & SVG Filter
st.markdown(
    """
<svg width="0" height="0" style="position:absolute;pointer-events:none;" aria-hidden="true">
  <defs>
    <filter id="page-goo">
      <feGaussianBlur in="SourceGraphic" stdDeviation="24" result="blur" />
      <feColorMatrix in="blur" mode="matrix" values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 22 -9" result="goo" />
      <feBlend in="SourceGraphic" in2="goo" />
    </filter>
  </defs>
</svg>
<div class="goo-field" aria-hidden="true">
  <div class="goo-layer">
    <div class="goo-blob gb1"></div>
    <div class="goo-blob gb2"></div>
    <div class="goo-blob gb3"></div>
    <div class="goo-blob gb4"></div>
  </div>
</div>
""",
    unsafe_allow_html=True,
)


def get_minio_pdf_names(storage_client):
    names = set()
    objects = storage_client.client.list_objects(
        storage_client.bucket_name, prefix="pdfs/", recursive=True
    )
    for obj in objects:
        if obj.object_name.lower().endswith(".pdf"):
            names.add(os.path.basename(obj.object_name))
    return names


def get_local_pdf_names():
    names = set()
    if not os.path.exists(LOCAL_PDFS_DIR):
        return names
    for entry in os.listdir(LOCAL_PDFS_DIR):
        full_path = os.path.join(LOCAL_PDFS_DIR, entry)
        if os.path.isfile(full_path) and entry.lower().endswith(".pdf"):
            names.add(entry)
    return names


def get_processed_markdown_names():
    """Return PDF filenames that have been processed into agents/markdown."""
    names = set()
    if not os.path.exists(LOCAL_MARKDOWN_DIR):
        return names

    for entry in os.listdir(LOCAL_MARKDOWN_DIR):
        entry_path = os.path.join(LOCAL_MARKDOWN_DIR, entry)
        if os.path.isdir(entry_path):
            has_md = any(
                os.path.isfile(os.path.join(entry_path, f)) and f.lower().endswith(".md")
                for f in os.listdir(entry_path)
            )
            if has_md:
                names.add(f"{entry}.pdf")
        elif os.path.isfile(entry_path) and entry.lower().endswith(".md"):
            names.add(f"{entry[:-3]}.pdf")
    return names


def status_badge(present):
    if present:
        return "<span class='ql-badge-yes'>Так</span>"
    return "<span class='ql-badge-no'>Ні</span>"


def col_header_html(title, yes_count, no_count):
    return (
        f"<th>"
        f"<div>{html.escape(title)}</div>"
        f"<div class='ql-th-stats'>"
        f"<span class='ql-stat-yes'>Так: {yes_count}</span>"
        f"<span class='ql-stat-no'>Ні: {no_count}</span>"
        f"</div>"
        f"</th>"
    )


def sync_static_pdfs(local_names):
    static_pdfs_dir = os.path.join(os.path.dirname(__file__), "static", "pdfs")
    os.makedirs(static_pdfs_dir, exist_ok=True)
    for name in local_names:
        dst = os.path.join(static_pdfs_dir, name)
        if not os.path.exists(dst):
            src = os.path.join(LOCAL_PDFS_DIR, name)
            try:
                os.link(src, dst)
            except OSError:
                pass


def file_name_html(name, in_local):
    safe_name = html.escape(name)
    if in_local:
        url = f"/app/static/pdfs/{urllib.parse.quote(name)}"
        return (
            f"<a class='ql-file-link' href='{url}' target='_blank' "
            f"rel='noopener noreferrer' title='Відкрити PDF ({safe_name})'>{safe_name}</a>"
        )
    return f"<span class='ql-file-name'>{safe_name}</span>"


def render_unified_table(filenames, minio_set, local_set, markdown_set):
    if not filenames:
        body_html = (
            "<div class='ql-empty'>Файлів не знайдено (перевірте фільтр або папки).</div>"
        )
    else:
        minio_yes = sum(1 for name in filenames if name in minio_set)
        local_yes = sum(1 for name in filenames if name in local_set)
        md_yes = sum(1 for name in filenames if name in markdown_set)
        total = len(filenames)

        rows = "".join(
            f"<tr>"
            f"<td><span class='ql-row-num'>{idx}</span></td>"
            f"<td>{file_name_html(name, name in local_set)}</td>"
            f"<td>{status_badge(name in local_set)}</td>"
            f"<td>{status_badge(name in minio_set)}</td>"
            f"<td>{status_badge(name in markdown_set)}</td>"
            f"</tr>"
            for idx, name in enumerate(filenames, 1)
        )
        body_html = f"""
        <div class="ql-table-scroll">
            <table class="ql-table">
                <thead>
                    <tr>
                        <th>#</th>
                        <th>Назва файлу</th>
                        {col_header_html("📁 agents/pdfs", local_yes, total - local_yes)}
                        {col_header_html("☁️ MinIO (pdfs/)", minio_yes, total - minio_yes)}
                        {col_header_html("📝 agents/markdown", md_yes, total - md_yes)}
                    </tr>
                </thead>
                <tbody>
                    {rows}
                </tbody>
            </table>
        </div>
        """

    st.markdown(
        f"""
        <div class="ql-table-panel">
            <div class="ql-col-header">
                <h3 class="ql-col-title">📋 Зведена таблиця наявності файлів</h3>
                <span class="ql-col-badge">{len(filenames)} файлів</span>
            </div>
            {body_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


# Initialize MinIO Storage
minio_available = False
minio_error = None
storage = None

try:
    from tools.storage_tools import MinioStorage

    storage = MinioStorage()
    minio_available = True
except Exception as e:
    minio_error = str(e)

# Sidebar
st.sidebar.markdown("### ⚖️ Legal Pipeline")
st.sidebar.caption("Керування PDF та Markdown файлами")
st.sidebar.markdown("---")

st.sidebar.markdown("#### 📦 Стан сховища MinIO")
if minio_available and storage:
    st.sidebar.markdown(
        "<span class='status-pill status-pill-green'>🟢 MinIO Connected</span>",
        unsafe_allow_html=True,
    )
    st.sidebar.caption(f"Bucket: `{storage.bucket_name}`")
    st.sidebar.caption(f"Endpoint: `{storage.endpoint}`")
else:
    st.sidebar.markdown(
        "<span class='status-pill status-pill-red'>🔴 MinIO Offline</span>",
        unsafe_allow_html=True,
    )
    st.sidebar.error(f"Помилка підключення:\n{minio_error}")

st.sidebar.markdown("---")
if st.sidebar.button("🔄 Оновити список", use_container_width=True):
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.caption("© 2026 Legal PDF & Markdown Manager")

# Main Page Header
st.markdown(
    "<div class='ql-eyebrow'>💧 QuickLiquid Glass UI · PDF & Markdown</div>",
    unsafe_allow_html=True,
)
st.markdown(
    "<h1 class='main-title'>⚖️ Керування <span class='ink'>PDF та Markdown</span></h1>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p class='ql-subtitle'>Зведена таблиця наявності PDF-документів у сховищі MinIO, папці <code>agents/pdfs</code> та оброблених файлів у <code>agents/markdown</code>.</p>",
    unsafe_allow_html=True,
)

# Fetch sets
minio_set = set()
if minio_available and storage:
    try:
        minio_set = get_minio_pdf_names(storage)
    except Exception as e:
        st.warning(f"Не вдалося отримати список PDF з MinIO: {e}")

local_set = get_local_pdf_names()
sync_static_pdfs(local_set)
markdown_set = get_processed_markdown_names()

all_files = sorted(
    minio_set | local_set | markdown_set,
    key=lambda name: (
        (name in minio_set) and (name in local_set) and (name in markdown_set),
        name.lower(),
    ),
)

SCRAPER_LOG_PATH = os.path.join(ROOT_DIR, "scratch", "scrape_pdfs.log")


def is_process_running(pid):
    try:
        waited_pid, _ = os.waitpid(pid, os.WNOHANG)
        if waited_pid == pid:
            return False
    except ChildProcessError:
        pass
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


# Summary Metrics & Action Button
if "scraper_active" not in st.session_state:
    st.session_state.scraper_active = False
    st.session_state.scraper_pid = None

if st.session_state.scraper_active and st.session_state.scraper_pid:
    if not is_process_running(st.session_state.scraper_pid):
        st.session_state.scraper_active = False
        st.session_state.scraper_pid = None

m1, m2, m3 = st.columns(3)
with m1:
    btn_label = (
        f"PDF у agents/pdfs\n\n**{len(local_set)}**\n\n⏳ Оновлення з сайту ВСУ..."
        if st.session_state.scraper_active
        else f"PDF у agents/pdfs\n\n**{len(local_set)}**\n\n🔄 Оновити з сайту ВСУ"
    )
    if st.button(
        btn_label,
        key="scrape_pdfs_btn",
        use_container_width=True,
        disabled=st.session_state.scraper_active,
        help="Запустити scrape_of_courtsite_pdfs.py для перевірки та завантаження нових PDF з сайту Верховного Суду",
    ):
        os.makedirs(os.path.dirname(SCRAPER_LOG_PATH), exist_ok=True)
        with open(SCRAPER_LOG_PATH, "w", encoding="utf-8") as f:
            f.write(
                f"=== [Оновлення з сайту Верховного Суду: {time.strftime('%Y-%m-%d %H:%M:%S')}] ===\n\n"
            )
        log_f = open(SCRAPER_LOG_PATH, "a", encoding="utf-8")
        proc = subprocess.Popen(
            [sys.executable, "-u", "agents/scrape_of_courtsite_pdfs.py"],
            cwd=ROOT_DIR,
            stdout=log_f,
            stderr=subprocess.STDOUT,
            text=True,
        )
        st.session_state.scraper_pid = proc.pid
        st.session_state.scraper_active = True
        st.rerun()

with m2:
    st.metric(label="PDF у MinIO (pdfs/)", value=f"{len(minio_set)}")
with m3:
    st.metric(label="Оброблено в agents/markdown", value=f"{len(markdown_set)}")

if os.path.exists(SCRAPER_LOG_PATH):
    with open(SCRAPER_LOG_PATH, "r", encoding="utf-8") as f:
        scraper_logs = f.read()
    with st.expander(
        "📝 Лог оновлення з сайту Верховного Суду",
        expanded=st.session_state.scraper_active,
    ):
        st.code(scraper_logs, language="bash")

if st.session_state.scraper_active:
    st.caption("⏳ Перевірка сайту Верховного Суду та завантаження нових файлів...")
    time.sleep(1.5)
    st.rerun()

st.markdown("---")

# Table Search Bar
search_query = st.text_input(
    "🔍 Пошук файлів за назвою",
    placeholder="🔍 Введіть назву або частину назви файлу (наприклад: Oglad_KCS_01_25)...",
    label_visibility="collapsed",
).strip().lower()

filtered_files = (
    [name for name in all_files if search_query in name.lower()]
    if search_query
    else all_files
)

# Unified Table
render_unified_table(filtered_files, minio_set, local_set, markdown_set)
