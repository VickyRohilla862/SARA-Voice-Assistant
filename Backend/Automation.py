from engine.router import handle_query

def main():
    print("Jarvis CLI started. Type 'exit' to quit.\n")

    while True:
        query = input(">>> ").strip()
        if query.lower() in ("exit", "quit"):
            break

        try:
            print(handle_query(query))
        except Exception as e:
            print("Error:", e)

if __name__ == "__main__":
    main()
