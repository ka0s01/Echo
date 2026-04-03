import os
import subprocess
from pathlib import Path

# ── Actual functions ──────────────────────────────

def read_file(path: str) -> str:
    try:
        content = []
        with open(path, "r", encoding='utf-8') as f:
            for line in f:
                content.append(line.rstrip())
        return "\n".join(content)
    except FileNotFoundError:
        return f"Error: File not found: {path}"
    except Exception as e:
        return f"Error reading file: {str(e)}"

def write_file(path: str, content: str) -> str:
    try:
        file_path = Path(path)
        os.makedirs(file_path.parent, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Successfully wrote to {path}"
    except Exception as e:
        return f"Error writing file: {str(e)}"

def append_file(path: str, content: str) -> str:
    try:
        file_path = Path(path)
        os.makedirs(file_path.parent, exist_ok=True)
        with open(path, 'a', encoding='utf-8') as f:
            f.write(content)
        return f"Successfully appended to {path}"
    except Exception as e:
        return f"Error appending to file: {str(e)}"

def list_directory(path: str) -> str:
    try:
        tree_str = ""
        for root, dirs, files in os.walk(path):
            dirs[:] = [d for d in dirs if d not in ['venv', '__pycache__', '.git', 'node_modules', '.idea']]
            level = root.replace(path, "").count(os.sep)
            indent = "│   " * level
            folder_name = os.path.basename(root)
            tree_str += f"{indent}├── {folder_name}/\n"
            sub_indent = "│   " * (level + 1)
            for file in files:
                tree_str += f"{sub_indent}├── {file}\n"
        return tree_str
    except Exception as e:
        return f"Error listing directory: {str(e)}"

def create_file(path: str, content: str) -> str:
    try:
        file_path = Path(path)
        if file_path.exists():
            return f"Error: File already exists: {path}"
        os.makedirs(file_path.parent, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"File created: {path}"
    except Exception as e:
        return f"Error creating file: {str(e)}"

def delete_file(path: str) -> str:
    try:
        file_path = Path(path)
        if not file_path.exists():
            return f"Error: File does not exist: {path}"
        if not file_path.is_file():
            return f"Error: Not a file: {path}"
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                backup = f.read()
        except Exception:
            backup = "[Binary or unreadable content]"
        os.remove(file_path)
        return f"File deleted: {path}. Backup content:\n{backup}"
    except Exception as e:
        return f"Error deleting file: {str(e)}"

def run_command(command: str) -> str:
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        output = ""
        if result.stdout:
            output += f"stdout:\n{result.stdout}"
        if result.stderr:
            output += f"stderr:\n{result.stderr}"
        if not output:
            output = "Command executed with no output."
        return output
    except subprocess.TimeoutExpired:
        return "Error: Command timed out after 30 seconds."
    except Exception as e:
        return f"Error running command: {str(e)}"


def search_in_files(query: str, path: str = ".") -> str:
    try:
        results = ""
        ignore = ['venv', '__pycache__', '.git', 'node_modules', '.idea']
        for root, dirs, files in os.walk(path):
            dirs[:] = [d for d in dirs if d not in ignore]
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        lines = f.readlines()
                    matches = [
                        f"  line {i+1}: {line.rstrip()}"
                        for i, line in enumerate(lines)
                        if query.lower() in line.lower()
                    ]
                    if matches:
                        results += f"\n{file_path}:\n" + "\n".join(matches) + "\n"
                except Exception:
                    continue  # skip binary or unreadable files
        return results if results else f"No matches found for '{query}'"
    except Exception as e:
        return f"Error searching files: {str(e)}"


# ── Tool dispatcher ───────────────────────────────
# This is how the agent calls tools by name at runtime

TOOL_FUNCTIONS = {
    "read_file": read_file,
    "write_file": write_file,
    "append_file": append_file,
    "list_directory": list_directory,
    "create_file": create_file,
    "delete_file": delete_file,
    "run_command": run_command,
    "search_in_files": search_in_files,
}

def execute_tool(tool_name: str, args: dict) -> str:
    if tool_name not in TOOL_FUNCTIONS:
        return f"Unknown tool: {tool_name}"
    return TOOL_FUNCTIONS[tool_name](**args)


# Tool schemas

TOOLS = [
    {
        "type":"function",
        "function":{
            "name":"read_file",
            "description":"Read the contents of a file",
            "parameters":{
                "type":"object",
                "properties":{
                    "path":{
                        "type":"string",
                        "description":"Path to the file to be read"
                    }
                },
                "required":["path"]
            }
            
            
        }
    },
    {
        "type":"function",
        "function":{
            "name":"write_file",
            "description":"Write the contents into a file, create if doesnt exist",
            "parameters":{
                "type":"object",
                "properties":{
                    "path":{
                        "type":"string",
                        "description":"Path to the file to be written"
                    },
                    "content":{
                        "type":"string",
                        "description":"Content to be written"
                    }
                },
                "required":["path","content"]
            }
            
        }
    },
    {
        "type":"function",
        "function":{
            "name":"append_file",
            "description":"Append the contents into a file, create if doesnt exist",
            "parameters":{
                "type":"object",
                "properties":{
                    "path":{
                        "type":"string",
                        "description":"Path to the file to append to"
                    },
                    "content":{
                        "type":"string",
                        "description":"Content to be appended"
                    }
                },
                "required":["path","content"]
            }
            
        }
    },
    {
        "type":"function",
        "function":{
            "name":"list_directory",
            "description":"Returns the directory tree as a readable string",
            "parameters":{
                "type":"object",
                "properties":{
                    "path":{
                        "type":"string",
                        "description":"Path of the directory"
                    }
                },
                "required":["path"]
            }
            
        }
    },
    {
    "type": "function",
    "function": {
        "name": "create_file",
        "description": "Creates a new file at the given path with the given content. Fails if file already exists.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the file to create"
                },
                "content": {
                    "type": "string",
                    "description": "Content to write into the new file"
                }
            },
            "required": ["path", "content"]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "delete_file",
        "description": "Deletes a file at the given path. Returns a backup of the content before deletion.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the file to delete"
                }
            },
            "required": ["path"]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "run_command",
        "description": "Runs a shell command and returns the output. Use for installing packages, running scripts, checking git status, running tests etc.",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "The shell command to run"
                }
            },
            "required": ["command"]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "search_in_files",
        "description": "Searches for a string across all files in a directory. Returns matching lines with filenames and line numbers.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The string to search for"
                },
                "path": {
                    "type": "string",
                    "description": "Directory to search in. Defaults to current directory."
                }
            },
            "required": ["query"]
        }
    }
}


]

if __name__ == "__main__":
    print(create_file("test.txt", "hello world"))
    print(read_file("test.txt"))
    print(append_file("test.txt", "\nsecond line"))
    print(read_file("test.txt"))
    print(list_directory("."))
    print(run_command("echo hi"))
    print(search_in_files("hello", "."))
    print(delete_file("test.txt"))