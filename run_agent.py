import sys
from agents.legal_segmenter import LegalSegmenterAgent

def main():
    try:
        target_file = sys.argv[1] if len(sys.argv) > 1 else None
        agent = LegalSegmenterAgent()
        agent.run(target_file)
    except Exception as e:
        print(f"🛑 Critical Agent Error: {e}")

if __name__ == "__main__":
    main()
