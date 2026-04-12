import os
import time
from rich.console import Console
from rich.prompt import Prompt, IntPrompt
from rich.progress import Progress, SpinnerColumn, TextColumn
from infrastructure.config import DEFAULT_CONFIG, CONFIG_FILE, load_config

def do_first_run_setup(force_setup=False):
    console = Console()

    needs_setup = force_setup
    if not os.path.exists(CONFIG_FILE):
        needs_setup = True
    else:
        try:
            with open(CONFIG_FILE, 'r') as f:
                import json
                data = json.load(f)
                if not data.get("api_key") or data.get("api_key") == "YOUR_API_KEY_HERE":
                    needs_setup = True
        except:
            needs_setup = True

    if needs_setup:
        config_data = DEFAULT_CONFIG.copy()
        if os.path.exists(CONFIG_FILE):
            try:
                config_data = load_config()
            except Exception:
                pass

        change_api = True
        change_folders = True

        if force_setup and os.path.exists(CONFIG_FILE):
            console.print("[bold cyan]What would you like to configure?[/bold cyan]")
            console.print("1) Everything")
            console.print("2) API & Provider only")
            console.print("3) Watch Folders only")
            choice = Prompt.ask("Choose an option by number", choices=["1", "2", "3"], default="1")

            if choice == "2":
                change_folders = False
            elif choice == "3":
                change_api = False

        console.clear()
        if not force_setup:
            console.print("[bold magenta]🌸 Welcome to Fuwa! 🌸[/bold magenta]\n")
            console.print("Let's set up your terminal buddy.\n")
        else:
            console.print("[bold magenta]🌸 Fuwa Configuration 🌸[/bold magenta]\n")

        if change_api:
            console.print("1) OpenAI")
            console.print("2) Anthropic")
            console.print("3) OpenRouter")

            while True:
                provider_choice_str = Prompt.ask("Choose your LLM provider by number", choices=["1", "2", "3"], default="1")
                try:
                    provider_choice = int(provider_choice_str)
                    break
                except ValueError:
                    console.print("[bold red]Please enter a valid integer number[/bold red]")

            provider = "openai"
            default_model = "gpt-4o-mini"
            if provider_choice == 2:
                provider = "anthropic"
                default_model = "claude-3-haiku-20240307"
            elif provider_choice == 3:
                provider = "openrouter"
                default_model = "openrouter/auto"

            if provider == "openai":
                console.print("\n[bold cyan]Available Models:[/bold cyan]")
                console.print("1) gpt-4o-mini (default, fastest)")
                console.print("2) gpt-4o")
                console.print("3) gpt-3.5-turbo")
                console.print("4) Custom (type it)")
                model_choice = Prompt.ask("Choose model by number", choices=["1", "2", "3", "4"], default="1")
                if model_choice == "1": model = "gpt-4o-mini"
                elif model_choice == "2": model = "gpt-4o"
                elif model_choice == "3": model = "gpt-3.5-turbo"
                else: model = Prompt.ask("Enter custom model name")
            elif provider == "anthropic":
                console.print("\n[bold cyan]Available Models:[/bold cyan]")
                console.print("1) claude-3-haiku-20240307 (default, fastest)")
                console.print("2) claude-3-sonnet-20240229")
                console.print("3) claude-3-opus-20240229")
                console.print("4) Custom (type it)")
                model_choice = Prompt.ask("Choose model by number", choices=["1", "2", "3", "4"], default="1")
                if model_choice == "1": model = "claude-3-haiku-20240307"
                elif model_choice == "2": model = "claude-3-sonnet-20240229"
                elif model_choice == "3": model = "claude-3-opus-20240229"
                else: model = Prompt.ask("Enter custom model name")
            else:
                model = Prompt.ask("Choose your model", default=default_model)

            while True:
                api_key = Prompt.ask("Enter your API key (will be saved in config.json)", password=True).strip()
                if not api_key:
                    console.print("[bold red]❌ Error: API key cannot be empty. Please try again.[/bold red]")
                else:
                    break

            config_data["provider"] = provider
            config_data["model"] = model
            config_data["api_key"] = api_key

        watch_folders = config_data.get("watch_folders", [os.path.expanduser('~')])
        if change_folders:
            home_dir = os.path.expanduser('~')
            console.print("\n[bold cyan]Select directories to observe:[/bold cyan]")
            console.print(f"1) Use home directory ({home_dir}) (default)")
            console.print("2) Open GUI folder picker")
            console.print("3) Type path manually")
            dir_choice = Prompt.ask("Choose option by number", choices=["1", "2", "3"], default="1")

            watch_folders_str = home_dir
            if dir_choice == "2":
                try:
                    import tkinter as tk
                    from tkinter import filedialog
                    root = tk.Tk()
                    root.withdraw()
                    root.attributes('-topmost', True)
                    folder = filedialog.askdirectory(title="Select directory to observe")
                    root.destroy()
                    if folder:
                        watch_folders_str = folder
                    else:
                        console.print("[yellow]No folder selected, falling back to manual input.[/yellow]")
                        watch_folders_str = Prompt.ask("Enter comma-separated directories to observe", default=home_dir)
                except Exception as e:
                    console.print(f"[yellow]GUI dialog failed ({e}), falling back to manual input.[/yellow]")
                    watch_folders_str = Prompt.ask("Enter comma-separated directories to observe", default=home_dir)
            elif dir_choice == "3":
                watch_folders_str = Prompt.ask("Enter comma-separated directories to observe", default=home_dir)

            watch_folders = [f.strip() for f in watch_folders_str.split(",") if f.strip()]
            if not watch_folders:
                watch_folders = [home_dir]

            config_data["watch_folders"] = watch_folders

        import json
        flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
        mode = 0o600
        fd = os.open(CONFIG_FILE, flags, mode)
        with os.fdopen(fd, "w") as f:
            json.dump(config_data, f, indent=4)
        os.chmod(CONFIG_FILE, 0o600)

        console.print("\n[bold green]✅ Setup complete![/bold green]\n")

        console.print("[bold cyan]Scanning directories to understand your project...[/bold cyan]")

        ignored_patterns = [
            ".git", "__pycache__", "node_modules", "venv", ".venv",
            "build", "dist", "target", ".idea", ".vscode", "memory.json", "config.json"
        ]

        def should_ignore(path_str):
            return any(f"/{pat}/" in path_str or path_str.endswith(f"/{pat}") or path_str.startswith(f"{pat}/") or path_str == pat for pat in ignored_patterns)

        with Progress(
            SpinnerColumn(spinner_name="dots"),
            TextColumn("[bold cyan]Analyzing project structure...[/bold cyan]"),
            transient=True
        ) as progress:
            task = progress.add_task("scanning", total=None)

            summaries = {}
            for folder in watch_folders:
                folder_path = os.path.abspath(folder)
                if not os.path.isdir(folder_path):
                    continue

                for root, dirs, files in os.walk(folder_path):
                    dirs[:] = [d for d in dirs if not should_ignore(os.path.join(root, d))]

                    for file in files:
                        filepath = os.path.join(root, file)
                        if should_ignore(filepath):
                            continue

                        try:
                            rel_path = os.path.relpath(filepath, os.getcwd())
                        except ValueError:
                            rel_path = filepath

                        summaries[rel_path] = f"File {rel_path} discovered during initial scan."

            if summaries:
                from infrastructure.memory import update_memories
                update_memories(summaries)

        console.print(f"[bold green]✅ Initial scan complete! Observed {len(summaries)} files.[/bold green]\n")

        with Progress(
            SpinnerColumn(spinner_name="dots"),
            TextColumn("[bold cyan]Waking up Fuwa...[/bold cyan]"),
            transient=True
        ) as progress:
            task = progress.add_task("waking", total=10)
            for _ in range(10):
                time.sleep(0.1)
                progress.update(task, advance=1)
