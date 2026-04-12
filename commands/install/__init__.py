import sys
import os
import subprocess
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

def handle():
    console.print(Panel("[bold magenta]🌸 Starting Fuwa Installation... 🌸[/bold magenta]", expand=False))
    if not os.path.exists("requirements.txt"):
        console.print(Panel("[bold red]❌ Error: requirements.txt not found.[/bold red]", title="Error", style="red"))
        sys.exit(1)

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            task = progress.add_task("[cyan]Installing dependencies...", total=None)

            cmd = [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

            stdout_data = ""
            for line in iter(process.stdout.readline, ''):
                stdout_data += line
                progress.update(task, advance=0.1)

            process.stdout.close()
            process.wait()

            if process.returncode != 0:
                console.print(Panel(f"[bold red]❌ Error: Failed to install dependencies.[/bold red]\n\n{stdout_data}", title="Error", style="red"))
                sys.exit(1)

            if not os.path.exists("venv"):
                os.makedirs("venv", exist_ok=True)
            with open("venv/.fuwa_installed", "w") as f:
                f.write("installed")

        console.print(Panel("[bold green]✅ Fuwa Installation Complete![/bold green]\nRun [bold cyan]./fuwa.sh run[/bold cyan] to start.", title="Success", style="green", expand=False))
    except KeyboardInterrupt:
        console.print(Panel("[bold yellow]⚠️ Installation aborted by user.[/bold yellow]", title="Aborted", style="yellow", expand=False))
        sys.exit(1)
