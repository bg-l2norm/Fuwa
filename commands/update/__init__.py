import sys
import os
import subprocess
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

def handle():
    console.print(Panel("[bold magenta]🌸 Updating Fuwa... 🌸[/bold magenta]", expand=False))
    if os.path.exists(".git"):
        console.print("[cyan]⬇️ Pulling latest changes from git...[/cyan]")

        try:
            old_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
        except subprocess.CalledProcessError:
            old_commit = None

        pull_process = subprocess.run(["git", "pull"], capture_output=True, text=True)
        if pull_process.returncode != 0:
            pull_process = subprocess.run(["git", "pull", "origin", "main"], capture_output=True, text=True)
            if pull_process.returncode != 0:
                console.print(Panel(f"[bold red]❌ Error: git pull failed. Please resolve conflicts manually.[/bold red]\n\n{pull_process.stderr or pull_process.stdout}", title="Error", style="red"))
                sys.exit(1)

        try:
            new_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
        except subprocess.CalledProcessError:
            new_commit = None

        if old_commit and new_commit and old_commit != new_commit:
            console.print("[bold green]✅ Successfully pulled latest changes.[/bold green]")
            try:
                from rich.table import Table
                diff_cmd = ["git", "diff", "--numstat", old_commit, new_commit]
                diff_output = subprocess.check_output(diff_cmd, text=True, stderr=subprocess.DEVNULL)
                if diff_output.strip():
                    table = Table(title="Updated Files", show_header=True, header_style="bold magenta")
                    table.add_column("Added (+)", style="green", justify="right")
                    table.add_column("Removed (-)", style="red", justify="right")
                    table.add_column("File", style="white")

                    for line in diff_output.strip().split('\n'):
                        parts = line.split('\t')
                        if len(parts) >= 3:
                            added, removed, filename = parts[0], parts[1], "\t".join(parts[2:])
                            added_str = f"+{added}" if added != '-' else "bin"
                            removed_str = f"-{removed}" if removed != '-' else "bin"
                            table.add_row(added_str, removed_str, filename)

                    console.print(table)
            except Exception as e:
                console.print(f"[yellow]Could not generate diff table: {e}[/yellow]")
        else:
            console.print("[cyan]Already up to date with the remote repository.[/cyan]")

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
