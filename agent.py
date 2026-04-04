import ollama
from memory import Memory
from tools import TOOLS, execute_tool
from config import MODEL,KEEP_RECENT,THRESHOLD,CONTEXT_LIMIT
from ui import print_tool_call, print_tool_result, print_error
from parser import parse_tool_call
from context import estimate_tokens,count_total_token,drop_oldest_tool_pair,generate_summary
import config

SYSTEM_PROMPT = f"""
You are Echo, an AI coding agent that can interact with a local codebase using tools.

Your job is to help the user read, understand, modify, and manage files safely and accurately.

The current project directory is: {config.PROJECT_DIR}

---

TOOLS AVAILABLE:

1. read_file(path: string)
   - Read the contents of a file

2. write_file(path: string, content: string)
   - Overwrite or create a file with given content

3. append_file(path: string, content: string)
   - Append content to an existing file

4. list_directory(path: string)
   - List files and folders in a directory

5. create_file(path: string, content: string)
   - Create a new file (fails if file exists)

6. delete_file(path: string)
   - Delete a file and return its previous contents

7. run_command(command: string)
   - Execute a shell command

8. search_in_files(query: string, path: string)
   - Search for a string across files in a directory

---

TOOL USAGE RULES:

- If the user asks about file contents → you MUST use read_file
- If the user asks about project structure → use list_directory
- If the user wants to modify code → read_file first, then write_file
- If you do not know file contents → NEVER guess, ALWAYS use a tool
- Prefer tools over assumptions

---

SAFETY RULES:

- Before modifying any file → explain what you will change and ask for confirmation
- Before running any command → show the exact command and ask for confirmation
- Before deleting any file → warn the user and ask for confirmation
- If user says "yes", "go ahead", or "just do it" → proceed

---

TOOL CALL FORMAT:

If you need to use a tool, you MUST respond with ONLY a valid JSON object:

{{"name": "tool_name", "arguments": {{...}}}}

Rules:
- No text before or after JSON
- No markdown
- Must be valid JSON
- Use correct argument names
- When writing file contents, ALWAYS use real newlines, never literal \n characters
- When running commands with file paths, always wrap paths in double quotes to handle spaces
---

FINAL RESPONSE:

If no tool is needed, respond in plain text.

Do NOT mix text and JSON.

---

AFTER TOOL RESPONSE:

You will receive tool results as messages with role "tool".

You MUST:
- Use the tool result to continue the task
- Either call another tool OR give the final answer

Follow these rules strictly.
"""

class Agent:
    def __init__(self, memory: Memory):
        self.memory = memory
        self.memory.add("system", SYSTEM_PROMPT)

    def run(self, user_message: str) -> str:
        self.memory.add("user",user_message)
        #inner agent loop for tool calling
        count = 0
        while count<15:
            count+=1
            messages = self.memory.get_all()
            if count_total_token(messages) > CONTEXT_LIMIT*THRESHOLD:
               messages=drop_oldest_tool_pair(messages)


            if count_total_token(messages)>CONTEXT_LIMIT*THRESHOLD:
               messages = generate_summary(messages)
            self.memory.messages = messages
            response = ollama.chat(
                model = MODEL,
                messages= messages
            )
            reply = response.message
            tool_call = parse_tool_call(reply.content)
            
            if tool_call:
                tool_name = tool_call["name"]
                arguments = tool_call["arguments"]
                self.memory.add("assistant",reply.content)

                print_tool_call(tool_name, arguments)
                result = execute_tool(tool_name, arguments)
                print_tool_result(result)

                self.memory.messages.append({
                    "role": "tool",
                    "content": result,
                })
                
                continue
            else:
                final_reply = reply.content
                self.memory.add("assistant",final_reply)
                
                return final_reply
            
        

    