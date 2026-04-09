# Fuwa 🌸

Fuwa is a minimalistic, rich TUI (Terminal User Interface) buddy powered by LLMs. It acts as an emotional, slightly demanding terminal companion (an axolotl!) that observes your high-level file activities and blurts out motivation, challenges, or fun comments.

![Fuwa](https://raw.githubusercontent.com/jules-ai/fuwa-assets/main/demo.png)

## Features
- **File System Observer:** Watches your folders for changes and understands when you are working hard or slacking off.
- **Dynamic Personality:** Fuwa's personality evolves based on your text-RPG style interactions with it.
- **Rich TUI:** A sleek, minimal Textual interface featuring a cute pixel-art style animated Axolotl.
- **LLM Powered:** Uses `litellm` under the hood, allowing you to use OpenAI, Anthropic, OpenRouter, or any other supported provider.

## Installation

1. Clone the repository.
2. Install the requirements:
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

Run the main application:
```bash
python fuwa.py
```

Fuwa will wake up, start observing your files, and interact with you!
