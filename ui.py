"""
ui.py — Echo TUI
Replaces the Rich scrolling UI with a full Textual TUI.

Layout:
  ┌─────────────┬──────────────────────────┬───────────────────┐
  │  File Tree  │       Chat Panel         │   Tool Call Log   │
  │  (left)     │       (center)           │   (right)         │
  │             │                          │                   │
  │             ├──────────────────────────┴───────────────────┤
  │             │  Input Box                                   │
  └─────────────┴──────────────────────────────────────────────┘

Threading model:
  - Textual event loop runs on the main thread (non-blocking, reactive)
  - Agent runs in a daemon background thread (blocking Ollama calls are fine here)
  - Agent communicates back via thread-safe queue + Textual's call_from_thread()
"""

from __future__ import annotations

import os
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, ScrollableContainer, Vertical
from textual.reactive import reactive
from textual.widgets import (
    DirectoryTree,
    Footer,
    Header,
    Input,
    Label,
    RichLog,
    Static,
)

# ─────────────────────────────────────────────
# Event types posted from the agent thread
# ─────────────────────────────────────────────

@dataclass
class AgentEvent:
    kind: str  # "user" | "assistant" | "tool_call" | "tool_result" | "error" | "system" | "thinking"
    text: str = ""
    tool_name: str = ""
    args: dict = field(default_factory=dict)


# ─────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────

ECHO_CSS = """
Screen {
    background: #0b0f14;
}

Header {
    background: #0b0f14;
    color: #d0d7e1;
    text-style: none;
    border-bottom: solid #1a2230;
}

#layout {
    layout: horizontal;
    height: 1fr;
}

/* ── Shared panel title ── */
.panel-title {
    
    color: #d0d7e1;
    text-style: bold;
    padding: 1 2;
     
}

/* ── Left: File Tree ── */
#tree-panel {
    width: 22;
    min-width: 18;
    border-right: solid #1a2230;
    background: #0b0f14;
}

DirectoryTree {
    background: #0b0f14;
    color: #6b778d;
    scrollbar-color: #1a2230;
    scrollbar-color-hover: #1a2230;
}

DirectoryTree > .tree--guides {
    color: #1e2a3a;
}

DirectoryTree:focus > .tree--cursor,
DirectoryTree .tree--cursor {
    background: #111820;
    color: #d0d7e1;
}

/* ── Center: Chat ── */
#chat-panel {
    width: 1fr;
    layout: vertical;
    border-right: solid #1a2230;
}

#chat-scroll {
    height: 1fr;
    background: #0b0f14;
    scrollbar-color: #1a2230;
    scrollbar-color-hover: #1a2230;
    padding: 0 1 1 1;
}

/* Message bubbles */
.msg-user {
    border: solid #2a5a40;
    background: #0b0f14;
    color: #d0d7e1;
    margin: 1 0 0 0;
    padding: 0 1;
    height: auto;
}

.msg-assistant {
    border: solid #1e3050;
    background: #0b0f14;
    color: #d0d7e1;
    margin: 1 0 0 0;
    padding: 0 1;
    height: auto;
}

.msg-label-user {
    color: #3a9a78;
    text-style: bold;
    margin: 1 0 0 1;
    height: 1;
}

.msg-label-assistant {
    color: #4a7ab5;
    text-style: bold;
    margin: 1 0 0 1;
    height: 1;
}

.msg-system {
    color: #3a4455;
    margin: 0 0 0 1;
    padding: 0;
    height: auto;
}

.msg-error {
    color: #7a3535;
    margin: 1 0 0 1;
    padding: 0;
    height: auto;
}

/* Welcome block */
#welcome-block {
    margin: 1 0 0 0;
    padding: 0 1;
    height: auto;
    color: #d0d7e1;
}

#input-bar {
    height: auto;
    padding: 0 1;
    border-top: solid #1a2230;
    background: #0b0f14;
}

#chat-input {
    border: solid #1a2230;
    background: #0b0f14;
    color: #d0d7e1;
    padding: 0 1;
}

#chat-input:focus {
    border: solid #3a9a78;
}

#thinking-indicator {
    color: #6b778d;
    text-style: italic;
    padding: 0 1;
    height: 1;
}

/* ── Right: Tool Log ── */
#tool-panel {
    width: 32;
    min-width: 24;
    background: #0b0f14;
    layout: vertical;
}

#tool-log {
    height: 1fr;
    background: #0b0f14;
    scrollbar-color: #1a2230;
    scrollbar-color-hover: #1a2230;
    padding: 0 1;
}

Footer {
    background: #0b0f14;
    color: #3a4455;
    border-top: solid #1a2230;
}
"""


# ─────────────────────────────────────────────
# Thinking indicator widget
# ─────────────────────────────────────────────

class ThinkingIndicator(Static):
    """Animated spinner shown while agent runs."""

    DEFAULT_CSS = ""
    _frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    _frame_idx = reactive(0)
    _visible = reactive(False)

    def on_mount(self) -> None:
        self.set_interval(0.1, self._tick)
        self.display = False

    def _tick(self) -> None:
        if self._visible:
            self._frame_idx = (self._frame_idx + 1) % len(self._frames)
            self.update(
                f"[dim]{self._frames[self._frame_idx]}[/] "
                "[dim italic]thinking...[/]"
            )

    def show(self) -> None:
        self._visible = True
        self.display = True

    def hide(self) -> None:
        self._visible = False
        self.display = False
        self.update("")


# ─────────────────────────────────────────────
# Main Textual App
# ─────────────────────────────────────────────

class EchoApp(App):
    """Echo TUI — the main application."""

    TITLE = "Echo"
    CSS = ECHO_CSS
    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit", priority=True),
        Binding("ctrl+l", "clear_chat", "Clear chat"),
        Binding("escape", "focus_input", "Focus input", show=False),
    ]

    def __init__(self, agent_runner: Callable[[str, Callable[[AgentEvent], None]], None]):
        super().__init__()
        self._agent_runner = agent_runner
        self._agent_thread: threading.Thread | None = None
        self._project_dir = Path(os.getcwd())

    # ── Layout ──────────────────────────────────

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal(id="layout"):
            # Left: file tree
            with Vertical(id="tree-panel"):
                yield Label("  Files", classes="panel-title")
                yield DirectoryTree(str(self._project_dir))

            # Center: chat + input
            with Vertical(id="chat-panel"):
                yield Label("  Chat", classes="panel-title")
                with ScrollableContainer(id="chat-scroll"):
                    yield Static(id="welcome-block")
                with Vertical(id="input-bar"):
                    yield ThinkingIndicator(id="thinking-indicator")
                    yield Input(
                        placeholder="  Message Echo  (Enter to send)",
                        id="chat-input",
                    )

            # Right: tool log
            with Vertical(id="tool-panel"):
                yield Label("  Tools", classes="panel-title")
                yield RichLog(id="tool-log", highlight=True, markup=True, wrap=True)

        yield Footer()

    def on_mount(self) -> None:
        self._render_welcome()
        self.query_one("#chat-input", Input).focus()

    # ── Input handling ───────────────────────────

    def on_input_submitted(self, event: Input.Submitted) -> None:
        text = event.value.strip()
        if not text:
            return
        event.input.value = ""

        if text.lower() in ("exit", "quit"):
            self.exit()
            return

        if text == "/clear":
            self.action_clear_chat()
            return

        self._append_chat_message("user", text)
        self._run_agent(text)

    # ── Agent threading ──────────────────────────

    def _run_agent(self, user_message: str) -> None:
        if self._agent_thread and self._agent_thread.is_alive():
            self._append_system("agent is still running, please wait.")
            return

        self.query_one("#chat-input", Input).disabled = True
        self.query_one(ThinkingIndicator).show()

        def target():
            try:
                self._agent_runner(user_message, self._on_agent_event)
            except Exception as exc:
                self.call_from_thread(
                    self._handle_agent_event, AgentEvent("error", str(exc))
                )
            finally:
                self.call_from_thread(self._agent_done)

        self._agent_thread = threading.Thread(target=target, daemon=True)
        self._agent_thread.start()

    def _on_agent_event(self, event: AgentEvent) -> None:
        self.call_from_thread(self._handle_agent_event, event)

    def _handle_agent_event(self, event: AgentEvent) -> None:
        if event.kind == "assistant":
            self._append_chat_message("assistant", event.text)
        elif event.kind == "tool_call":
            self._append_tool_call(event.tool_name, event.args)
        elif event.kind == "tool_result":
            self._append_tool_result(event.text)
        elif event.kind == "error":
            self._append_error(event.text)
        elif event.kind == "system":
            self._append_system(event.text)

    def _agent_done(self) -> None:
        self.query_one(ThinkingIndicator).hide()
        inp = self.query_one("#chat-input", Input)
        inp.disabled = False
        inp.focus()

    # ── Chat rendering ───────────────────────────

    def _render_welcome(self) -> None:
        block = self.query_one("#welcome-block", Static)
        block.update(
            "[bold #d0d7e1]"
            "  ███████╗ ██████╗██╗  ██╗ ██████╗ \n"
            "  ██╔════╝██╔════╝██║  ██║██╔═══██╗\n"
            "  █████╗  ██║     ███████║██║   ██║\n"
            "  ██╔══╝  ██║     ██╔══██║██║   ██║\n"
            "  ███████╗╚██████╗██║  ██║╚██████╔╝\n"
            "  ╚══════╝ ╚═════╝╚═╝  ╚═╝ ╚═════╝ \n"
            "[/bold #d0d7e1]\n"
            f"[dim]  ┌─────────────────────────────────────────────┐\n"
            f"  │[/dim]  [#6b778d]Project[/#6b778d]   [#d0d7e1]{self._project_dir}[/#d0d7e1]\n"
            f"[dim]  │[/dim]  [#6b778d]Model[/#6b778d]     [#d0d7e1]qwen2.5-coder:14b via Ollama[/#d0d7e1]\n"
            f"[dim]  ├─────────────────────────────────────────────┤\n"
            f"  │[/dim]  [#6b778d]/clear[/#6b778d]    Reset conversation memory\n"
            f"[dim]  │[/dim]  [#6b778d]exit[/#6b778d]      Quit Echo\n"
            f"[dim]  └─────────────────────────────────────────────┘[/dim]"
        )

    def _scroll_to_bottom(self) -> None:
        scroll = self.query_one("#chat-scroll", ScrollableContainer)
        scroll.scroll_end(animate=False)

    def _append_chat_message(self, role: str, text: str) -> None:
        scroll = self.query_one("#chat-scroll", ScrollableContainer)
        if role == "user":
            scroll.mount(Label("  you", classes="msg-label-user"))
            scroll.mount(Static(text, classes="msg-user"))
        elif role == "assistant":
            scroll.mount(Label("  echo", classes="msg-label-assistant"))
            scroll.mount(Static(text, classes="msg-assistant"))
        self.call_after_refresh(self._scroll_to_bottom)

    def _append_error(self, text: str) -> None:
        scroll = self.query_one("#chat-scroll", ScrollableContainer)
        scroll.mount(Static(f"error: {text}", classes="msg-error"))
        self.call_after_refresh(self._scroll_to_bottom)

    def _append_system(self, text: str) -> None:
        scroll = self.query_one("#chat-scroll", ScrollableContainer)
        scroll.mount(Static(text, classes="msg-system"))
        self.call_after_refresh(self._scroll_to_bottom)

    # ── Tool log rendering ───────────────────────

    def _append_tool_call(self, tool_name: str, args: dict) -> None:
        log = self.query_one("#tool-log", RichLog)
        args_str = "\n".join(f"  [dim]{k}[/dim]  {v}" for k, v in args.items())
        log.write(f"\n[#3a9a78]+ {tool_name}[/#3a9a78]\n{args_str}\n")

    def _append_tool_result(self, result: str) -> None:
        log = self.query_one("#tool-log", RichLog)
        preview = result[:400] + ("..." if len(result) > 400 else "")
        log.write(f"[dim]  {preview}[/dim]\n")

    # ── Actions ──────────────────────────────────

    def action_clear_chat(self) -> None:
        scroll = self.query_one("#chat-scroll", ScrollableContainer)
        # Remove all mounted message widgets except the welcome block
        for widget in scroll.query(".msg-user, .msg-assistant, .msg-system, .msg-error, .msg-label-user, .msg-label-assistant"):
            widget.remove()
        self.query_one("#tool-log", RichLog).clear()
        self._append_system("memory cleared.")

    def action_focus_input(self) -> None:
        self.query_one("#chat-input", Input).focus()


# ─────────────────────────────────────────────
# Public API — called from main.py / agent.py
# ─────────────────────────────────────────────

_emit: Callable[[AgentEvent], None] | None = None


def emit(event: AgentEvent) -> None:
    if _emit is not None:
        _emit(event)


def print_user(message: str) -> None:
    emit(AgentEvent("user", message))

def print_assistant(message: str) -> None:
    emit(AgentEvent("assistant", message))

def print_tool_call(tool_name: str, args: dict) -> None:
    emit(AgentEvent("tool_call", tool_name=tool_name, args=args))

def print_tool_result(result: str) -> None:
    emit(AgentEvent("tool_result", result))

def print_error(message: str) -> None:
    emit(AgentEvent("error", message))

def print_system(message: str) -> None:
    emit(AgentEvent("system", message))

def print_welcome() -> None:
    pass  # handled by TUI on mount


def run_tui(agent_runner: Callable[[str, Callable[[AgentEvent], None]], None]) -> None:
    """
    Entry point. Call this from main.py instead of the old REPL loop.

    agent_runner signature:
        def agent_runner(user_message: str, emit: Callable[[AgentEvent], None]) -> None
    """
    app = EchoApp(agent_runner)
    app.run()