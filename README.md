# Echo 

This is a  CLI-based AI agent that runs in your terminal, reads and writes files in your project, and helps you understand, edit, and manage code. Think Claude Code but local (Ollama)

To use it all you have to do is CD into ur project folder and enter echo-start in ur terminal

---

## Stack

- **Model:** `qwen2.5-coder:14b` via Ollama (local, no API key needed)
- **UI:** Rich (pretty terminal output)
- **Memory:** Conversation history stored in-process

---

## Setup
 
**1. Clone and install globally** (do NOT use a venv — needs to be a global install so `echo-start` is available everywhere)
 
```bash
git clone https://github.com/yourname/echo
cd echo
pip install -e .
```
 
**2. Add Python Scripts to your PATH**
 
After installing, pip will warn you that `echo-start.exe` was installed in a folder that's not on your PATH. You need to add it manually.
 
On **Windows**:
- Press `Win + S` and search "Environment Variables"
- Click "Edit the system environment variables" → "Environment Variables"
- Under User variables, find `Path` and click Edit
- Add a new entry — it'll be something like:
  ```
  C:\Users\YourName\AppData\Roaming\Python\Python3XX\Scripts
  ```
  (the exact path is printed in the pip warning when you install)
- Click OK and open a new terminal
 
On **Mac/Linux**, add this to your `~/.bashrc` or `~/.zshrc`:
```bash
export PATH="$HOME/Library/Python/3.x/bin:$PATH"  # Mac
export PATH="$HOME/.local/bin:$PATH"               # Linux
```
Then run `source ~/.bashrc` or `source ~/.zshrc`.
 
**3. Pull the model and start Ollama**
 
```bash
ollama pull qwen2.5-coder:14b
ollama serve
```
---

## Usage

`cd` into any project you want to work on and just type:

```bash
cd /your/project
echo-start
```

That's it. Echo picks up the current folder as the working directory and all file operations happen there.

---

## Commands

| Command  | What it does         |
|----------|----------------------|
| `exit`   | Quit                 |
| `/clear` | Reset conversation memory |

---

## How tool calling works (and why it's done manually here)

`qwen2.5-coder:14b` is the model i used here and unfortunately it does not support native tool calling :(  when you pass the tool schema to OLLAMA it just ignores it,so Echo
uses "Prompt Engineered function calling instread"

- The system prompt describes all available tools and tells the model to respond with a raw JSON object when it wants to use one — no markdown, no explanation, just JSON
- A custom parser (`parser.py`) extracts that JSON from the model's response
- The agent dispatches the tool call, gets the result, feeds it back into the conversation, and loops until the model gives a plain text final response

It's the same idea as native tool calling, just done manually.

### Want to use a smarter model?

If you swap in a model that actually supports native tool calling (GPT-4o, Claude, Gemini etc.), you can ditch the manual parsing and use proper tool calling instead.

For **Ollama models that support it** you have to change `agent.py`:

```python
response = ollama.chat(
    model=MODEL,
    messages=self.memory.get_all(),
    tools=TOOLS  # pass tools here
)

# Then check response.message.tool_calls instead of parsing content
if response.message.tool_calls:
    for tool in response.message.tool_calls:
        result = execute_tool(tool.function.name, tool.function.arguments)
        ...
```
We just pass the tool schema and just check tool_calls int he response instead of parsing it
The rest of the agent loop stays the same.


---

## Preview

<img width="900" height="330" alt="image" src="https://github.com/user-attachments/assets/e5a7345f-3533-4ba9-b7ad-6691bb841f3f" />
<img width="900" height="330" alt="image" src="https://github.com/user-attachments/assets/d9a6f95e-559e-407c-921a-929ec34cf245" />
<img width="900" height="330" alt="image" src="https://github.com/user-attachments/assets/ed29577b-4b73-4574-9d04-6fc734c07cfa" />
<img width="900" height="330" alt="image" src="https://github.com/user-attachments/assets/61072baf-90cb-4aa1-9607-235d8b0f9034" />



---


## Project structure

```
echo/
├── main.py        # Entry point, chat loop
├── agent.py       # Agent loop, tool dispatch
├── tools.py       # Tool implementations + schema
├── parser.py      # Extracts tool call JSON from model output
├── memory.py      # Conversation history
├── ui.py          # Terminal UI (Rich)
├── config.py      # Model name, project dir
└── context.py     # (coming soon) Token-aware context management
```
--- 
## Functionality im still working on 

- [x] Core agent loop with tool calling
- [x] File read/write/create/delete tools
- [x] Shell command execution
- [ ] `context.py` — smart context window management for large projects
- [ ] Diff preview before file changes
- [ ] Confirmation prompts before destructive actions
- [ ] `/explain` and `/review` commands
- [ ] MCP server — expose Echo's tools to other clients
