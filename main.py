import ollama 
from ui import *
from memory import *
from config import PROJECT_DIR
memory = Memory()

def run():
    print_welcome()
    print_system(f"Working dir: {PROJECT_DIR}")

    while True:
        try:
            user_input = input("\n ").strip()
            print("\033[A\033[K", end="")

            if not user_input:
                continue

            if user_input == "/clear":
                memory.clear()
                print_system("Memory Cleared\n")
                continue
            
            if user_input == "exit":
                print_system("Exitting \n")
                break

            print_user(user_input)

            memory.add("user",user_input)
            response = ollama.chat(
                model="qwen2.5-coder",
                messages=memory.get_all()
            )

            reply = response['message']['content']
            memory.add("assistant",reply)
            print_assistant(reply)
        except KeyboardInterrupt:
            print_system("\n Keyboard Interrup - Goodby")
            break
        except Exception as e:
            print_error(str(e))

if __name__ == "__main__":
    run()

