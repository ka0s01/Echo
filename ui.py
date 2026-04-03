from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.rule import Rule

console = Console()

def print_user(message: str):
    console.print(Panel(f"\n[bold cyan]You:[/bold cyan] {message}",border_style="cyan"))

def print_assistant(message: str):
    console.print("\n[bold green]Echo:[/bold green]")
    console.print(Panel(Markdown(message),border_style="green"))

def print_tool_call(tool_name: str, args: dict):
    args_str = ", ".join(f"{k}: {v}" for k, v in args.items())
    console.print(f"\n[bold yellow]→ {tool_name}[/bold yellow] [dim]({args_str})[/dim]")

def print_tool_result(result: str):
    console.print(f"[dim]  ✓ {result[:100]}{'...' if len(result) > 100 else ''}[/dim]")

def print_error(message: str):
    console.print(f"\n[bold red]Error:[/bold red] {message}")

def print_system(message: str):
    console.print(f"[dim italic]{message}[/dim italic]")

def print_divider():
    console.print(Rule(style="dim"))

def print_welcome():
    console.print(Panel(
        "[bold green]ECHO[/bold green]\n"
        "[dim]Powered by qwen2.5-coder via Ollama[/dim]\n\n"
        "Type [bold]exit[/bold] to quit\n"
        "Type [bold]/clear[/bold] to reset memory",
        title="Welcome",
        border_style="green"
    ))

