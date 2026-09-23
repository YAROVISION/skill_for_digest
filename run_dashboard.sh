#!/bin/bash
# Script to launch the Legal AI Agent Streamlit Dashboard

echo "🚀 Starting Legal AI Agent Dashboard..."
echo "📂 Project root: $(pwd)"

# Check if streamlit is installed
if ! python3 -c "import streamlit" &> /dev/null; then
    echo "⚠️ Streamlit is not installed or not in python3 path. Installing dependencies first..."
    python3 -m pip install -r requirements.txt
fi

# Run the app
python3 -m streamlit run dashboard/app.py --browser.gatherUsageStats=false --server.port 8501 --server.address 0.0.0.0
