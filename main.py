from ui import print_welcome, print_user, print_assistant, print_error, print_system
from memory import Memory
from agent import Agent
import config

memory = Memory()
agent = Agent(memory)

def run():
    print_welcome()
    print_system(f"Working directory: {config.PROJECT_DIR}")

    while True:
        try:
            user_input = input("\n> ").strip()
            print("\033[A\033[K", end="")

            if not user_input:
                continue

            if user_input == "/clear":
                memory.clear()
                print_system("Memory cleared.")
                continue

            if user_input == "exit":
                print_system("Goodbye.")
                break

            print_user(user_input)
            response = agent.run(user_input)
            print_assistant(response)

        except KeyboardInterrupt:
            print_system("\nGoodbye.")
            break
        except Exception as e:
            print_error(str(e))

if __name__ == "__main__":
    run()