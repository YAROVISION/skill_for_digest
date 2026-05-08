from agents.legal_segmenter import LegalSegmenterAgent

def main():
    try:
        agent = LegalSegmenterAgent()
        agent.run()
    except Exception as e:
        print(f"🛑 Critical Agent Error: {e}")

if __name__ == "__main__":
    main()
