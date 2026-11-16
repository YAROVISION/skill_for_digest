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
SCRAPER_LOG_PATH = os.path.join(ROOT_DIR, "scratch", "scrape_pdfs.log")
SYNC_LOG_PATH = os.path.join(ROOT_DIR, "scratch", "sync_minio.log")
CONVERTER_LOG_PATH = os.path.join(ROOT_DIR, "scratch", "convert_md.log")
DOWNLOAD_HISTORY_PATH = os.path.join(ROOT_DIR, "agents", "lists", "download_history.md")

THEMES = {
    "Лате": {
        "swatches": ["#5A5059", "#92887F", "#B8ADAB", "#D7EEF3", "#D18E5F"],
        "vars": {
            "--bg": "#262126",
            "--bg-soft": "#3a3339",
            "--panel-rgb": "90, 80, 89",
            "--soft-rgb": "58, 51, 57",
            "--acc-rgb": "209, 142, 95",
            "--ice-rgb": "215, 238, 243",
            "--line-rgb": "184, 173, 171",
            "--blob-1": "rgba(209, 142, 95, 0.46)",
            "--blob-2": "rgba(215, 238, 243, 0.34)",
            "--blob-3": "rgba(146, 136, 127, 0.44)",
            "--blob-4": "rgba(90, 80, 89, 0.65)",
            "--text": "#D7EEF3",
            "--muted": "#B8ADAB",
            "--faint": "#92887F",
            "--acc-a": "#D18E5F",
            "--acc-b": "#D7EEF3",
            "--acc-c": "#B8ADAB",
            "--copper": "#D18E5F",
            "--silver": "#B8ADAB",
            "--taupe": "#92887F",
            "--ice": "#D7EEF3",
            "--grad": "linear-gradient(95deg, #D18E5F, #B8ADAB 48%, #D7EEF3)",
        },
    },
    "Сланець": {
        "swatches": ["#353C52", "#554A53", "#726364", "#9A686B", "#BA897A"],
        "vars": {
            "--bg": "#1f2433",
            "--bg-soft": "#353C52",
            "--panel-rgb": "53, 60, 82",
            "--soft-rgb": "53, 60, 82",
            "--acc-rgb": "186, 137, 122",
            "--ice-rgb": "232, 222, 218",
            "--line-rgb": "154, 104, 107",
            "--blob-1": "rgba(186, 137, 122, 0.42)",
            "--blob-2": "rgba(154, 104, 107, 0.38)",
            "--blob-3": "rgba(85, 74, 83, 0.55)",
            "--blob-4": "rgba(53, 60, 82, 0.72)",
            "--text": "#EFE6E3",
            "--muted": "#BA897A",
            "--faint": "#9A686B",
            "--acc-a": "#BA897A",
            "--acc-b": "#9A686B",
            "--acc-c": "#726364",
            "--copper": "#BA897A",
            "--silver": "#9A686B",
            "--taupe": "#726364",
            "--ice": "#EFE6E3",
            "--grad": "linear-gradient(95deg, #BA897A, #9A686B 52%, #EFE6E3)",
        },
    },
    "Літо": {
        "swatches": ["#D1ECE7", "#FEE16C", "#BD7F01", "#A23D01", "#22352C"],
        "vars": {
            "--bg": "#16231d",
            "--bg-soft": "#22352C",
            "--panel-rgb": "34, 53, 44",
            "--soft-rgb": "34, 53, 44",
            "--acc-rgb": "254, 225, 108",
            "--ice-rgb": "209, 236, 231",
            "--line-rgb": "209, 236, 231",
            "--blob-1": "rgba(254, 225, 108, 0.34)",
            "--blob-2": "rgba(209, 236, 231, 0.28)",
            "--blob-3": "rgba(189, 127, 1, 0.36)",
            "--blob-4": "rgba(162, 61, 1, 0.34)",
            "--text": "#D1ECE7",
            "--muted": "#a6d3cb",
            "--faint": "#75a69d",
            "--acc-a": "#FEE16C",
            "--acc-b": "#BD7F01",
            "--acc-c": "#A23D01",
            "--copper": "#FEE16C",
            "--silver": "#a6d3cb",
            "--taupe": "#BD7F01",
            "--ice": "#D1ECE7",
            "--grad": "linear-gradient(95deg, #FEE16C, #BD7F01 52%, #D1ECE7)",
        },
    },
    "Місто": {
        "swatches": ["#102020", "#2D4C4F", "#78B4B7", "#D9E9E9", "#83241E"],
        "vars": {
            "--bg": "#102020",
            "--bg-soft": "#2D4C4F",
            "--panel-rgb": "45, 76, 79",
            "--soft-rgb": "30, 52, 54",
            "--acc-rgb": "120, 180, 183",
            "--ice-rgb": "217, 233, 233",
            "--line-rgb": "120, 180, 183",
            "--blob-1": "rgba(120, 180, 183, 0.38)",
            "--blob-2": "rgba(217, 233, 233, 0.26)",
            "--blob-3": "rgba(131, 36, 30, 0.42)",
            "--blob-4": "rgba(45, 76, 79, 0.68)",
            "--text": "#D9E9E9",
            "--muted": "#9ec6c8",
            "--faint": "#78B4B7",
            "--acc-a": "#78B4B7",
            "--acc-b": "#D9E9E9",
            "--acc-c": "#83241E",
            "--copper": "#78B4B7",
            "--silver": "#9ec6c8",
            "--taupe": "#78B4B7",
            "--ice": "#D9E9E9",
            "--grad": "linear-gradient(95deg, #78B4B7, #D9E9E9 52%, #c9564e)",
        },
    },
}

# Set page configurations
st.set_page_config(
    page_title="pdf_md — Legal PDF & Markdown Manager",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

if "theme" not in st.session_state or st.session_state.theme not in THEMES:
    st.session_state.theme = "Лате"

# Load QuickLiquid CSS Styles
styles_path = os.path.join(os.path.dirname(__file__), "styles.css")
if os.path.exists(styles_path):
    with open(styles_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Apply selected theme CSS variable overrides
active_vars = THEMES[st.session_state.theme]["vars"]
theme_css = "\n".join(f"    {k}: {v};" for k, v in active_vars.items())
st.markdown(f"<style>:root {{\n{theme_css}\n}}</style>", unsafe_allow_html=True)

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


def get_processed_markdown_map():
    """Return mapping {pdf_filename: relative_md_path} for files in agents/markdown."""
    md_map = {}
    if not os.path.exists(LOCAL_MARKDOWN_DIR):
        return md_map

    for entry in os.listdir(LOCAL_MARKDOWN_DIR):
        entry_path = os.path.join(LOCAL_MARKDOWN_DIR, entry)
        if os.path.isdir(entry_path):
            md_files = sorted(
                f for f in os.listdir(entry_path)
                if os.path.isfile(os.path.join(entry_path, f)) and f.lower().endswith(".md")
            )
            if md_files:
                md_map[f"{entry}.pdf"] = f"{entry}/{md_files[0]}"
        elif os.path.isfile(entry_path) and entry.lower().endswith(".md"):
            md_map[f"{entry[:-3]}.pdf"] = entry
    return md_map


def status_badge(present):
    if present:
        return "<span class='ql-badge-yes'>Так</span>"
    return "<span class='ql-badge-no'>Ні</span>"


def markdown_status_badge(rel_md_path):
    if rel_md_path:
        url = f"?md={urllib.parse.quote(rel_md_path)}"
        return (
            f"<a class='ql-badge-yes ql-badge-link' href='{url}' "
            f"title='Відкрити в редакторі: {html.escape(rel_md_path)}'>Так</a>"
        )
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


def sync_static_files(local_names, markdown_map):
    static_root = os.path.join(os.path.dirname(__file__), "static")
    static_pdfs_dir = os.path.join(static_root, "pdfs")
    static_md_dir = os.path.join(static_root, "markdown")
    os.makedirs(static_pdfs_dir, exist_ok=True)
    os.makedirs(static_md_dir, exist_ok=True)

    for name in local_names:
        dst = os.path.join(static_pdfs_dir, name)
        if not os.path.exists(dst):
            src = os.path.join(LOCAL_PDFS_DIR, name)
            try:
                os.link(src, dst)
            except OSError:
                pass

    for rel_md_path in markdown_map.values():
        dst = os.path.join(static_md_dir, rel_md_path)
        if not os.path.exists(dst):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            src = os.path.join(LOCAL_MARKDOWN_DIR, rel_md_path)
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


def render_unified_table(filenames, minio_set, local_set, markdown_map):
    if not filenames:
        body_html = (
            "<div class='ql-empty'>Файлів не знайдено (перевірте фільтр або папки).</div>"
        )
    else:
        minio_yes = sum(1 for name in filenames if name in minio_set)
        local_yes = sum(1 for name in filenames if name in local_set)
        md_yes = sum(1 for name in filenames if name in markdown_map)
        total = len(filenames)

        rows = "".join(
            f"<tr>"
            f"<td><span class='ql-row-num'>{idx}</span></td>"
            f"<td>{file_name_html(name, name in local_set)}</td>"
            f"<td>{status_badge(name in local_set)}</td>"
            f"<td>{status_badge(name in minio_set)}</td>"
            f"<td>{markdown_status_badge(markdown_map.get(name))}</td>"
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


# Top Header Bar: Brand (pdf_md) Left + Theme Switcher Right
hdr_left, hdr_right = st.columns([6, 1.4])
with hdr_left:
    st.markdown(
        """
        <div class="ql-brand">
            <span class="ql-logo-badge" aria-hidden="true">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" style="color: var(--bg);">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                    <polyline points="14 2 14 8 20 8"></polyline>
                    <line x1="8" y1="13" x2="16" y2="13"></line>
                    <line x1="8" y1="17" x2="13" y2="17"></line>
                </svg>
            </span>
            <span class="ql-brand-name">pdf_md</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

with hdr_right:
    dot_cols = st.columns(len(THEMES), gap="small")
    for idx, theme_name in enumerate(THEMES):
        is_active = st.session_state.theme == theme_name
        with dot_cols[idx]:
            if st.button(
                " ",
                key=f"theme_dot_{theme_name}",
                help=f"Тема: {theme_name}",
                type="primary" if is_active else "secondary",
            ):
                st.session_state.theme = theme_name
                st.rerun()

# Main Page Title
st.markdown(
    "<h1 class='main-title'><span class='ink'>PDF_MD</span></h1>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p class='ql-subtitle'>Зведена таблиця наявності PDF-документів у сховищі MinIO, папці <code>agents/pdfs</code> та оброблених файлів у <code>agents/markdown</code>.</p>",
    unsafe_allow_html=True,
)

# Initialize MinIO Storage
minio_available = False
storage = None

try:
    from tools.storage_tools import MinioStorage

    storage = MinioStorage()
    minio_available = True
except Exception:
    pass

# Fetch sets
minio_set = set()
if minio_available and storage:
    try:
        minio_set = get_minio_pdf_names(storage)
    except Exception as e:
        st.warning(f"Не вдалося отримати список PDF з MinIO: {e}")

local_set = get_local_pdf_names()
markdown_map = get_processed_markdown_map()
markdown_set = set(markdown_map.keys())
sync_static_files(local_set, markdown_map)

all_files = sorted(
    minio_set | local_set | markdown_set,
    key=lambda name: (
        (name in minio_set) and (name in local_set) and (name in markdown_set),
        name.lower(),
    ),
)

# Summary Metrics & Action Buttons
if "scraper_active" not in st.session_state:
    st.session_state.scraper_active = False
    st.session_state.scraper_pid = None

if "sync_active" not in st.session_state:
    st.session_state.sync_active = False
    st.session_state.sync_pid = None

if "converter_active" not in st.session_state:
    st.session_state.converter_active = False
    st.session_state.converter_pid = None

if st.session_state.scraper_active and st.session_state.scraper_pid:
    if not is_process_running(st.session_state.scraper_pid):
        st.session_state.scraper_active = False
        st.session_state.scraper_pid = None

if st.session_state.sync_active and st.session_state.sync_pid:
    if not is_process_running(st.session_state.sync_pid):
        st.session_state.sync_active = False
        st.session_state.sync_pid = None

if st.session_state.converter_active and st.session_state.converter_pid:
    if not is_process_running(st.session_state.converter_pid):
        st.session_state.converter_active = False
        st.session_state.converter_pid = None

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
    sync_btn_label = (
        f"PDF у MinIO (pdfs/)\n\n**{len(minio_set)}**\n\n⏳ Синхронізація з agents/pdfs..."
        if st.session_state.sync_active
        else f"PDF у MinIO (pdfs/)\n\n**{len(minio_set)}**\n\n🔁 Синхронізувати з agents/pdfs"
    )
    if st.button(
        sync_btn_label,
        key="sync_minio_btn",
        use_container_width=True,
        disabled=st.session_state.sync_active,
        help="Двостороння синхронізація PDF-файлів між MinIO (pdfs/) та локальною папкою agents/pdfs",
    ):
        os.makedirs(os.path.dirname(SYNC_LOG_PATH), exist_ok=True)
        with open(SYNC_LOG_PATH, "w", encoding="utf-8") as f:
            f.write(
                f"=== [Синхронізація MinIO ↔ agents/pdfs: {time.strftime('%Y-%m-%d %H:%M:%S')}] ===\n\n"
            )
        sync_log_f = open(SYNC_LOG_PATH, "a", encoding="utf-8")
        sync_proc = subprocess.Popen(
            [sys.executable, "-u", "agents/sync_pdfs.py"],
            cwd=ROOT_DIR,
            stdout=sync_log_f,
            stderr=subprocess.STDOUT,
            text=True,
        )
        st.session_state.sync_pid = sync_proc.pid
        st.session_state.sync_active = True
        st.rerun()
with m3:
    md_btn_label = (
        f"Оброблено в agents/markdown\n\n**{len(markdown_set)}**\n\n⏳ Конвертація PDF у MD..."
        if st.session_state.converter_active
        else f"Оброблено в agents/markdown\n\n**{len(markdown_set)}**\n\n📝 Конвертувати PDF у MD"
    )
    if st.button(
        md_btn_label,
        key="convert_md_btn",
        use_container_width=True,
        disabled=st.session_state.converter_active,
        help="Запустити convert_pdfs_to_md.py для перетворення нових PDF у Markdown",
    ):
        os.makedirs(os.path.dirname(CONVERTER_LOG_PATH), exist_ok=True)
        with open(CONVERTER_LOG_PATH, "w", encoding="utf-8") as f:
            f.write(
                f"=== [Конвертація PDF у Markdown: {time.strftime('%Y-%m-%d %H:%M:%S')}] ===\n\n"
            )
        conv_log_f = open(CONVERTER_LOG_PATH, "a", encoding="utf-8")
        conv_proc = subprocess.Popen(
            [sys.executable, "-u", "agents/convert_pdfs_to_md.py"],
            cwd=ROOT_DIR,
            stdout=conv_log_f,
            stderr=subprocess.STDOUT,
            text=True,
        )
        st.session_state.converter_pid = conv_proc.pid
        st.session_state.converter_active = True
        st.rerun()

with st.expander(
    "📜 Журнал скачаних файлів (agents/lists/download_history.md)",
    expanded=st.session_state.scraper_active,
):
    if os.path.exists(DOWNLOAD_HISTORY_PATH):
        with open(DOWNLOAD_HISTORY_PATH, "r", encoding="utf-8") as f:
            history_content = f.read().strip()
        if history_content:
            st.markdown(history_content)
        else:
            st.info("Журнал скачувань поки порожній.")
    else:
        st.info("Файл журналу `agents/lists/download_history.md` ще не створено (нових скачувань не було).")

if os.path.exists(SYNC_LOG_PATH):
    with open(SYNC_LOG_PATH, "r", encoding="utf-8") as f:
        sync_logs = f.read()
    with st.expander(
        "🔁 Лог синхронізації MinIO ↔ agents/pdfs",
        expanded=st.session_state.sync_active,
    ):
        st.code(sync_logs, language="bash")

if os.path.exists(CONVERTER_LOG_PATH):
    with open(CONVERTER_LOG_PATH, "r", encoding="utf-8") as f:
        converter_logs = f.read()
    with st.expander(
        "📝 Лог конвертації PDF у Markdown",
        expanded=st.session_state.converter_active,
    ):
        st.code(converter_logs, language="bash")

if st.session_state.scraper_active or st.session_state.sync_active or st.session_state.converter_active:
    if st.session_state.scraper_active:
        st.caption("⏳ Перевірка сайту Верховного Суду та завантаження нових файлів...")
    if st.session_state.sync_active:
        st.caption("⏳ Синхронізація PDF-файлів між MinIO та agents/pdfs...")
    if st.session_state.converter_active:
        st.caption("⏳ Конвертація нових PDF-файлів у Markdown...")
    time.sleep(1.5)
    st.rerun()

def render_markdown_editor(markdown_map, selected_rel_path):
    import markdown as md_lib

    all_md_paths = sorted(markdown_map.values(), key=str.lower)
    if not all_md_paths:
        st.info("У папці `agents/markdown` поки немає жодного `.md` файлу.")
        return

    if selected_rel_path not in all_md_paths:
        selected_rel_path = all_md_paths[0]

    nav_col1, nav_col2 = st.columns([1.4, 4.6])
    with nav_col1:
        if st.button("← Назад до таблиці", use_container_width=True):
            st.session_state.editor_open = False
            st.query_params.clear()
            st.rerun()
    with nav_col2:
        chosen_path = st.selectbox(
            "Оберіть Markdown-файл",
            options=all_md_paths,
            index=all_md_paths.index(selected_rel_path),
            label_visibility="collapsed",
        )
        if chosen_path != selected_rel_path:
            st.query_params["md"] = chosen_path
            st.rerun()

    full_md_path = os.path.realpath(os.path.join(LOCAL_MARKDOWN_DIR, chosen_path))
    if not full_md_path.startswith(os.path.realpath(LOCAL_MARKDOWN_DIR) + os.sep):
        st.error("Некоректний шлях до файлу.")
        return

    with open(full_md_path, "r", encoding="utf-8") as f:
        original_text = f.read()

    editor_key = f"md_editor_{chosen_path}"
    if editor_key not in st.session_state:
        st.session_state[editor_key] = original_text

    edit_col, preview_col = st.columns(2)
    with edit_col:
        st.markdown(f"#### ✏️ Редактор · `{chosen_path}`")
        edited_text = st.text_area(
            "Вміст Markdown",
            key=editor_key,
            height=650,
            label_visibility="collapsed",
        )
        act1, act2 = st.columns(2)
        with act1:
            if st.button("💾 Зберегти зміни", type="primary", use_container_width=True):
                with open(full_md_path, "w", encoding="utf-8") as f:
                    f.write(edited_text)
                st.toast(f"Збережено: {os.path.basename(chosen_path)}")
                st.success("✅ Зміни успішно збережено!")
        with act2:
            st.download_button(
                label="📥 Скачати .md",
                data=edited_text,
                file_name=os.path.basename(chosen_path),
                mime="text/markdown",
                use_container_width=True,
            )

    with preview_col:
        st.markdown("#### 👁️ Попередній перегляд")
        rendered_html = md_lib.markdown(
            edited_text,
            extensions=["tables", "fenced_code", "nl2br"],
        )
        st.markdown(
            f"<div class='ql-md-preview'>{rendered_html}</div>",
            unsafe_allow_html=True,
        )


st.markdown("---")

query_md = st.query_params.get("md")
if query_md:
    st.session_state.editor_open = True

if st.session_state.get("editor_open"):
    render_markdown_editor(markdown_map, query_md)
else:
    # Table Search Bar + Editor Button
    bar_col1, bar_col2 = st.columns([5, 1.3])
    with bar_col1:
        search_query = st.text_input(
            "🔍 Пошук файлів за назвою",
            placeholder="🔍 Введіть назву або частину назви файлу (наприклад: Oglad_KCS_01_25)...",
            label_visibility="collapsed",
        ).strip().lower()
    with bar_col2:
        if st.button("📝 Редактор MD", use_container_width=True):
            st.session_state.editor_open = True
            st.rerun()

    filtered_files = (
        [name for name in all_files if search_query in name.lower()]
        if search_query
        else all_files
    )

    # Unified Table
    render_unified_table(filtered_files, minio_set, local_set, markdown_map)
