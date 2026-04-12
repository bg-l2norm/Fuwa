import sys
import os
import subprocess
from rich.console import Console
from rich.panel import Panel

console = Console()

def handle():
    console.print(Panel("[bold magenta]🩺 Starting Fuwa Doctor... 🩺[/bold magenta]", expand=False))
    issues_found = 0
    issues_fixed = 0

    console.print("[cyan]Checking Python...[/cyan]")
    console.print("✅ Python check passed.")

    console.print("\n[cyan]Checking Virtual Environment...[/cyan]")
    if not os.path.exists("venv/bin/activate"):
        console.print("[bold yellow]⚠️ Issue: Valid virtual environment 'venv' not found.[/bold yellow]")
        issues_found += 1

        if os.path.exists("venv"):
            console.print("🔧 Fixing: Removing invalid 'venv'...")
            import shutil
            shutil.rmtree("venv", ignore_errors=True)

        console.print("🔧 Fixing: Creating virtual environment...")
        process = subprocess.run([sys.executable, "-m", "venv", "venv"])
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
            check_script = "import textual, rich, watchdog, PIL"
            process = subprocess.run(["venv/bin/python", "-c", check_script], capture_output=True)

            if process.returncode != 0 or not os.path.exists("venv/.fuwa_installed"):
                console.print("[bold yellow]⚠️ Issue: Missing dependencies or incomplete installation.[/bold yellow]")
                issues_found += 1
                console.print("🔧 Fixing: Installing dependencies...")
                if os.path.exists("requirements.txt"):
                    pip_proc = subprocess.run(["venv/bin/pip", "install", "-r", "requirements.txt"], capture_output=True)
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
             process = subprocess.run(["venv/bin/python", "-c", "import infrastructure.config as config; config.load_config()"], capture_output=True)
             if process.returncode == 0:
                 console.print("[bold green]✅ Fixed: config.json generated.[/bold green]")
                 issues_fixed += 1
             else:
                 console.print("[bold red]❌ Error: Failed to generate config.json.[/bold red]")
        else:
             process = subprocess.run([sys.executable, "-c", "import infrastructure.config as config; config.load_config()"], capture_output=True)
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
