import sys
import os
import subprocess
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

def handle():
    console.print(Panel("[bold magenta]🌸 Updating Fuwa... 🌸[/bold magenta]", expand=False))
    console.print("[cyan]Skipping git pull to preserve local LOC-1 refactor.[/cyan]")

    if not os.path.exists("requirements.txt"):
        console.print(Panel("[bold red]❌ Error: requirements.txt not found.[/bold red]", title="Error", style="red"))
        sys.exit(1)

    if not (os.path.exists("venv/bin/activate") and os.path.exists("venv/.fuwa_installed")):
        console.print(Panel("[bold yellow]⚠️ Virtual environment not found or incomplete. Please run './fuwa.sh install' first.[/bold yellow]", title="Warning", style="yellow"))
        sys.exit(1)

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            task = progress.add_task("[cyan]Updating dependencies...", total=None)

            cmd = [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

            stdout_data = ""
            for line in iter(process.stdout.readline, ''):
                stdout_data += line
                progress.update(task, advance=0.1)

            process.stdout.close()
            process.wait()

            if process.returncode != 0:
                console.print(Panel(f"[bold red]❌ Error: Failed to update dependencies.[/bold red]\n\n{stdout_data}", title="Error", style="red"))
                sys.exit(1)

        console.print(Panel("[bold green]✅ Fuwa updated successfully![/bold green]", title="Success", style="green", expand=False))
    except KeyboardInterrupt:
        console.print(Panel("[bold yellow]⚠️ Update aborted by user.[/bold yellow]", title="Aborted", style="yellow", expand=False))
        sys.exit(1)
