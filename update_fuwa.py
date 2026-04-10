import re

with open('fuwa.py', 'r') as f:
    content = f.read()

# Update imports
content = content.replace(
    'from textual.widgets import Header, Footer, Static, Input, Button, Log, Label',
    'from textual.widgets import Header, Footer, Static, Input, Button, Log, Label, RichLog'
)
content = content.replace(
    'from config import load_config',
    'from config import load_config, update_config, CONFIG_FILE'
)

# Update CSS
content = content.replace(
    '#chat_log {',
    '#chat_log {\n        height: 1fr;\n        border-bottom: dashed $secondary;\n    }\n    #rich_log {'
) # Just in case it's styled differently, let's just make sure both exist or replace it
content = re.sub(r'#chat_log \{[^}]+\}', '#chat_log {\n        height: 1fr;\n        border-bottom: dashed $secondary;\n    }', content)


# Update widget yields
content = content.replace(
    'yield Log(id="chat_log", highlight=True)',
    'yield RichLog(id="chat_log", markup=True)'
)

# Update on_mount
content = content.replace(
    'self.chat_log_view = self.query_one("#chat_log", Log)',
    'self.chat_log_view = self.query_one("#chat_log", RichLog)'
)

# Update write_line
content = content.replace(
    'self.chat_log_view.write_line(formatted)',
    'self.chat_log_view.write(formatted)'
)


# Add do_first_run_setup
setup_logic = """
def do_first_run_setup():
    import os
    import time
    from rich.console import Console
    from rich.prompt import Prompt
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from config import DEFAULT_CONFIG, CONFIG_FILE

    console = Console()

    # Determine if we need to run setup
    needs_setup = False
    if not os.path.exists(CONFIG_FILE):
        needs_setup = True
    else:
        # Check if API key is empty
        try:
            with open(CONFIG_FILE, 'r') as f:
                import json
                data = json.load(f)
                if not data.get("api_key") or data.get("api_key") == "YOUR_API_KEY_HERE":
                    needs_setup = True
        except:
            needs_setup = True

    if needs_setup:
        console.clear()
        console.print("[bold magenta]🌸 Welcome to Fuwa! 🌸[/bold magenta]\\n")
        console.print("Let's set up your terminal buddy.\\n")

        provider = Prompt.ask("Choose your LLM provider", choices=["openai", "anthropic", "openrouter"], default="openai")

        default_model = "gpt-4o-mini"
        if provider == "anthropic":
            default_model = "claude-3-haiku-20240307"
        elif provider == "openrouter":
            default_model = "openrouter/auto"

        model = Prompt.ask("Choose your model", default=default_model)
        api_key = Prompt.ask("Enter your API key (will be saved in config.json)", password=True)

        config_data = DEFAULT_CONFIG.copy()
        config_data["provider"] = provider
        config_data["model"] = model
        config_data["api_key"] = api_key

        with open(CONFIG_FILE, "w") as f:
            import json
            json.dump(config_data, f, indent=4)

        console.print("\\n[bold green]✅ Setup complete![/bold green]\\n")

        # Aesthetic loader
        with Progress(
            SpinnerColumn(spinner_name="dots"),
            TextColumn("[bold cyan]Waking up Fuwa...[/bold cyan]"),
            transient=True
        ) as progress:
            progress.add_task("waking", total=None)
            time.sleep(2.0)
"""

# Insert setup logic before App class
content = content.replace('class FuwaApp(App):', setup_logic + '\nclass FuwaApp(App):')

# Update __main__
main_logic = """if __name__ == "__main__":
    do_first_run_setup()
    app = FuwaApp()
    app.run()"""
content = re.sub(r'if __name__ == "__main__":\n    app = FuwaApp\(\)\n    app\.run\(\)', main_logic, content)


with open('fuwa.py', 'w') as f:
    f.write(content)

print("Done")
