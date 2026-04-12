import sys
from rich.console import Console
from commands import discover

console = Console()

def main():
    if len(sys.argv) < 2:
        console.print("Usage: python installer.py [install|update|doctor]")
        sys.exit(1)

    command_name = sys.argv[1]
    registry = discover()

    if command_name in registry:
        registry[command_name]()
    else:
        console.print(f"[bold red]❌ Unknown command: {command_name}[/bold red]")
        sys.exit(1)

if __name__ == "__main__":
    main()
