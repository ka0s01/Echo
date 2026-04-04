# Echo 

This is a  CLI-based AI agent that runs in your terminal, reads and writes files in your project, and helps you understand, edit, and manage code. Think Claude Code but local (Ollama)

To use it all you have to do is CD into ur project folder and enter echo-start in ur terminal

---

## Stack

- **Model:** `qwen2.5-coder:14b` via Ollama 
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

---

## Context Engineering
LLMs have a fixed context window for the model i used its 32,000 tokens.
Context engineering ensures that what you send to the model is worth the tokens it costs.

### How it works

Echo tracks token usage after every turn. When the message history crosses 80% of the context window (~25,600 tokens), compression kicks in in two stages:

Stage 1 — Drop old tool pairs. Tool results are the fattest and most disposable messages — once the agent has acted on them, the raw data has no future value. Echo removes the oldest assistant+tool message pairs first.

Stage 2 — Summarize. If dropping tool pairs isn't enough, Echo compresses the remaining old messages into a single summary message using the model itself.

### What is always preserved

- System prompt — Echo's identity, tools, and safety rules
- Last 15 messages — enough context for the current task
- Summary message if one exists


---

## Want to use a smarter model?

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

### updated TUI
<img width="1866" height="931" alt="image" src="https://github.com/user-attachments/assets/555d8f19-cd31-4017-9d3c-bcceab46c372" />
<img width="1868" height="942" alt="image" src="https://github.com/user-attachments/assets/48be6220-2acb-406d-8f86-91823cfe000f" />
<img width="1893" height="955" alt="image" src="https://github.com/user-attachments/assets/e9760f09-de8d-41b0-9270-4fcdc5090535" />

## old TUI
<img width="1000" height="811" alt="Screenshot 2026-04-04 165257" src="https://github.com/user-attachments/assets/5933ea04-52c2-47b1-abe3-6c5ffce95f33" />
<img width="1000" height="839" alt="Screenshot 2026-04-04 165305" src="https://github.com/user-attachments/assets/2d6cca96-4400-4fa3-bbfa-ef1ff3b712b0" />
<img width="1000" height="851" alt="Screenshot 2026-04-04 165314" src="https://github.com/user-attachments/assets/f3578fdd-d216-4467-a20b-6a8ca5fd291a" />
<img width="1000" height="795" alt="Screenshot 2026-04-04 165334" src="https://github.com/user-attachments/assets/a52a7c5d-2d79-499d-a702-a986883865e2" />
<img width="1000" height="640" alt="Screenshot 2026-04-04 165341" src="https://github.com/user-attachments/assets/27183874-6a71-486f-a7c2-9f6db13b3285" />


---

## Functionality im still working on 

- [x] Core agent loop with tool calling
- [x] File read/write/create/delete tools
- [x] Shell command execution
- [x] `context.py` — smart context window management for large projects
- [ ] Diff preview before file changes
- [ ] Confirmation prompts before destructive actions
- [ ] MCP server — expose Echo's tools to other clients
