# Fuwa 🌸

![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Terminal](https://img.shields.io/badge/terminal-TUI-purple.svg)
![LLM](https://img.shields.io/badge/LLM-Powered-orange.svg)

Fuwa is a minimalistic, rich TUI (Terminal User Interface) buddy powered by LLMs. It acts as an emotional, slightly demanding terminal companion (an axolotl!) that observes your high-level file activities and blurts out motivation, challenges, or fun comments.

![Fuwa](https://raw.githubusercontent.com/jules-ai/fuwa-assets/main/demo.png)

![Axolotl](assets/normal_1.png)

## Features

| Feature | Description |
| :--- | :--- |
| 📁 **File System Observer** | Watches your folders for changes and understands when you are working hard or slacking off. |
| 🎭 **Dynamic Personality** | Fuwa's personality evolves based on your text-RPG style interactions with it. |
| ✨ **Rich TUI** | A sleek, minimal Textual interface featuring a cute pixel-art style animated Axolotl. |
| 🧠 **LLM Powered** | Uses `litellm` under the hood, allowing you to use OpenAI, Anthropic, OpenRouter, or any other supported provider. |

## Automated Scripts (Recommended)

For a simple and automated experience, use the provided `fuwa.sh` script.

```bash
# Install Fuwa (creates isolated venv and installs dependencies)
./fuwa.sh install

# Run Fuwa
./fuwa.sh run

# Or just run it without arguments to launch
./fuwa.sh

# Update Fuwa (pulls latest code and updates dependencies)
./fuwa.sh update

# Troubleshooting (checks environment and dependencies, fixes basic issues)
./fuwa.sh doctor
```

## Manual Installation

To avoid dependency conflicts with other projects on your system (dependency hell), it is highly recommended to install Fuwa inside an isolated virtual environment.

1. Clone the repository.
2. Create and activate a Python virtual environment:
   ```bash
   # Create a virtual environment named 'venv'
   python3 -m venv venv

   # Activate the environment (Linux/macOS)
   source venv/bin/activate

   # Activate the environment (Windows)
   venv\Scripts\activate
   ```
3. Install the requirements into the isolated environment:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

On first run, Fuwa generates a `config.json` file in the root directory. You must configure it with your desired LLM provider and API key.

```json
{
    "watch_folders": [
        "."
    ],
    "provider": "openai",
    "model": "gpt-4o-mini",
    "api_key": "YOUR_API_KEY_HERE",
    "personality": "You are Fuwa, a cute, slightly sarcastic, and extremely motivating axolotl terminal companion..."
}
```

- **`watch_folders`**: An array of absolute or relative paths to directories you want Fuwa to observe.
- **`provider`**: E.g., `openai`, `anthropic`, `openrouter`.
- **`model`**: E.g., `gpt-4o-mini`, `claude-3-haiku-20240307`, `openrouter/auto`.

## Running Fuwa

Run the main application (the automated script handles activating the environment for you):
```bash
./fuwa.sh run
```
Or manually:
```bash
source venv/bin/activate
python fuwa.py
```

Fuwa will wake up, start observing your files, and interact with you!

## Testing

To run the test suite, ensure your virtual environment is activated, then use:
```bash
python -m pytest test_fuwa.py
```
