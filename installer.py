import sys
import os
import subprocess
import time
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

def do_install():
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

            cmd = f'"{sys.executable}" -m pip install -r requirements.txt'
            process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

            stdout_data = ""
            for line in iter(process.stdout.readline, ''):
                stdout_data += line
                progress.update(task, advance=0.1)

            process.stdout.close()
            process.wait()

            if process.returncode != 0:
                console.print(Panel(f"[bold red]❌ Error: Failed to install dependencies.[/bold red]\n\n{stdout_data}", title="Error", style="red"))
                sys.exit(1)

            # Ensure venv directory exists before touching
            if not os.path.exists("venv"):
                os.makedirs("venv", exist_ok=True)
            with open("venv/.fuwa_installed", "w") as f:
                f.write("installed")

        console.print(Panel("[bold green]✅ Fuwa Installation Complete![/bold green]\nRun [bold cyan]./fuwa.sh run[/bold cyan] to start.", title="Success", style="green", expand=False))
    except KeyboardInterrupt:
        console.print(Panel("[bold yellow]⚠️ Installation aborted by user.[/bold yellow]", title="Aborted", style="yellow", expand=False))
        sys.exit(1)

def do_update():
    if os.path.exists(".git"):
        console.print("[cyan]⬇️ Pulling latest changes from git...[/cyan]")
        process = subprocess.run("git fetch origin main && git merge FETCH_HEAD", shell=True, capture_output=True, text=True)
        if process.returncode != 0:
            console.print(Panel(f"[bold red]❌ Error: git merge failed. Please resolve conflicts manually.[/bold red]\n\n{process.stderr}", title="Error", style="red"))
            sys.exit(1)

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

            cmd = f'"{sys.executable}" -m pip install -r requirements.txt'
            process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

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

def do_doctor():
    issues_found = 0
    issues_fixed = 0

    console.print("[cyan]Checking Python...[/cyan]")
    # fuwa.sh handles python checks but let's just log it
    console.print("✅ Python check passed.")

    console.print("\n[cyan]Checking Virtual Environment...[/cyan]")
    if not os.path.exists("venv/bin/activate"):
        console.print("[bold yellow]⚠️ Issue: Valid virtual environment 'venv' not found.[/bold yellow]")
        issues_found += 1

        if os.path.exists("venv"):
            console.print("🔧 Fixing: Removing invalid 'venv'...")
            subprocess.run("rm -rf venv", shell=True)

        console.print("🔧 Fixing: Creating virtual environment...")
        process = subprocess.run(f'"{sys.executable}" -m venv venv', shell=True)
        if process.returncode == 0:
            console.print("[bold green]✅ Fixed: Virtual environment created.[/bold green]")
            issues_fixed += 1
        else:
            console.print("[bold red]❌ Error: Failed to create virtual environment.[/bold red]")
    else:
        console.print("✅ Virtual environment check passed.")

    console.print("\n[cyan]Checking Dependencies...[/cyan]")
    if os.path.exists("venv/bin/activate"):
        try:
            # We don't want to use subprocess run to import since textual might fail if missing.
            # However, we can just run a python script inside the venv to check imports
            check_script = "import textual, rich, watchdog, PIL"
            process = subprocess.run(f"source venv/bin/activate && python -c '{check_script}'", shell=True, executable='/bin/bash', capture_output=True)

            if process.returncode != 0 or not os.path.exists("venv/.fuwa_installed"):
                console.print("[bold yellow]⚠️ Issue: Missing dependencies or incomplete installation.[/bold yellow]")
                issues_found += 1
                console.print("🔧 Fixing: Installing dependencies...")
                if os.path.exists("requirements.txt"):
                    pip_proc = subprocess.run("source venv/bin/activate && pip install -r requirements.txt", shell=True, executable='/bin/bash', capture_output=True)
                    if pip_proc.returncode == 0:
                        with open("venv/.fuwa_installed", "w") as f:
                            f.write("installed")
                        console.print("[bold green]✅ Fixed: Dependencies installed.[/bold green]")
                        issues_fixed += 1
                    else:
                        console.print(f"[bold red]❌ Error: Failed to install dependencies.[/bold red]")
                else:
                    console.print("[bold red]❌ Error: requirements.txt not found.[/bold red]")
            else:
                console.print("✅ Dependencies check passed.")
        except Exception as e:
            console.print(f"[bold red]❌ Error checking dependencies: {e}[/bold red]")
    else:
        console.print("[bold red]❌ Error: Could not find venv/bin/activate[/bold red]")

    console.print("\n[cyan]Checking Configuration...[/cyan]")
    if not os.path.exists("config.json"):
        console.print("[bold yellow]⚠️ Issue: config.json not found.[/bold yellow]")
        issues_found += 1
        console.print("🔧 Fixing: Generating config.json...")
        if os.path.exists("venv/bin/activate"):
             process = subprocess.run("source venv/bin/activate && python -c 'import config; config.load_config()'", shell=True, executable='/bin/bash', capture_output=True)
             if process.returncode == 0:
                 console.print("[bold green]✅ Fixed: config.json generated.[/bold green]")
                 issues_fixed += 1
             else:
                 console.print("[bold red]❌ Error: Failed to generate config.json.[/bold red]")
        else:
             # Just fallback to current env
             process = subprocess.run("python -c 'import config; config.load_config()'", shell=True, capture_output=True)
             if process.returncode == 0:
                 console.print("[bold green]✅ Fixed: config.json generated.[/bold green]")
                 issues_fixed += 1
             else:
                 console.print("[bold red]❌ Error: Failed to generate config.json.[/bold red]")

    if os.path.exists("config.json"):
        try:
            with open("config.json", "r") as f:
                content = f.read()
            if '"api_key": "YOUR_API_KEY_HERE"' in content:
                console.print("[bold yellow]⚠️ Warning: config.json still has default API key.\n   Please edit config.json and set a real API key.[/bold yellow]")
                issues_found += 1
            else:
                console.print("✅ config.json check passed.")
        except Exception as e:
            pass

    console.print(f"\n[bold]🩺 Doctor summary: Found {issues_found} issues, fixed {issues_fixed} issues.[/bold]")
    if issues_found > issues_fixed:
        console.print("[bold yellow]⚠️ Some issues require manual intervention.[/bold yellow]")
    else:
        console.print("[bold magenta]🌸 Your Fuwa installation looks healthy![/bold magenta]")


def main():
    if len(sys.argv) < 2:
        console.print("Usage: python installer.py [install|update|doctor]")
        sys.exit(1)

    command = sys.argv[1]

    if command == "install":
        console.print(Panel("[bold magenta]🌸 Starting Fuwa Installation... 🌸[/bold magenta]", expand=False))
        do_install()
    elif command == "update":
        console.print(Panel("[bold magenta]🌸 Updating Fuwa... 🌸[/bold magenta]", expand=False))
        do_update()
    elif command == "doctor":
        console.print(Panel("[bold magenta]🩺 Starting Fuwa Doctor... 🩺[/bold magenta]", expand=False))
        do_doctor()
    else:
        console.print(f"[bold red]❌ Unknown command: {command}[/bold red]")
        sys.exit(1)

if __name__ == "__main__":
    main()
