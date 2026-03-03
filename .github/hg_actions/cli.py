import typer
import json
import sys
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from .parser import parse_markdown_action
from .planner import Planner
from .executor import Executor
from .config import settings

app = typer.Typer(help="HGActions: AI-Driven Workflow Automation")
console = Console()

@app.command()
def run(
    action_file: str = typer.Argument(..., help="Path to the Markdown action file"),
    execute: bool = typer.Option(True, "--execute/--dry-run", help="Execute the plan immediately or just show it")
):
    """
    Run an HGActions workflow file.
    """
    console.print(f"[bold blue]HGActions[/bold blue] loading [bold]{action_file}[/bold]...")

    # 1. Parse
    try:
        with open(action_file, "r") as f:
            action_data = parse_markdown_action(f.read())
    except FileNotFoundError:
        console.print(f"[bold red]Error:[/bold red] File {action_file} not found.")
        raise typer.Exit(code=1)

    console.print(Panel(f"Title: {action_data['title']}\nDescription: {action_data.get('description', '')}", title="Action Loaded", border_style="green"))

    # 2. Plan
    console.print("[yellow]Generating Execution Plan (via AI)...[/yellow]")
    planner = Planner()
    plan = planner.create_plan(action_data)

    console.print("\n[bold]Generated Plan:[/bold]")
    console.print_json(json.dumps(plan))

    if not execute:
        console.print("[blue]Dry run complete. Use --execute to run.[/blue]")
        return

    # 3. Execute
    if Confirm.ask("\nExecute this plan?", default=True):
        console.print("\n[bold green]Starting Execution...[/bold green]")
        executor = Executor()
        executor.execute_plan(plan)
        console.print("\n[bold green]Success![/bold green]")
    else:
        console.print("[red]Aborted.[/red]")

@app.command()
def config():
    """
    Show current configuration.
    """
    console.print(Panel(f"""
[bold]OpenAI Base URL:[/bold] {settings.openai_base_url}
[bold]Proxy Repo:[/bold] {settings.hga_proxy_repo or "Not Set"}
[bold]GitHub Token:[/bold] {"Set" if settings.github_token else "Not Set"}
    """, title="Configuration", border_style="blue"))

@app.command()
def start_daemon(
    workflow_file: str = typer.Argument(..., help="Path to the JSON5 workflow file"),
    repo_path: str = typer.Option(".", help="Root of the repository to manage")
):
    """
    Starts the HGActions Autonomous Daemon.
    """
    console.print(f"[bold green]Starting Autonomous Daemon[/bold green]")
    console.print(f"Workflow: {workflow_file}")
    console.print(f"Repo: {repo_path}")

    try:
        from .autonomous import run_daemon
    except ModuleNotFoundError as e:
        console.print(f"[bold red]Error:[/bold red] Cannot start daemon: {e}")
        raise typer.Exit(code=1)

    try:
        run_daemon(workflow_file, repo_path)
    except KeyboardInterrupt:
        console.print("\n[yellow]Daemon stopped by user.[/yellow]")

if __name__ == "__main__":
    app()
