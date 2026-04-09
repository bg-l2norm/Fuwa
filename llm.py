import json
import litellm
import os
from config import load_config

def _get_api_kwargs():
    config = load_config()
    model = config.get("model", "gpt-4o-mini")
    provider = config.get("provider", "openai")
    api_key = config.get("api_key", "")

    if not api_key or api_key == "YOUR_API_KEY_HERE":
        raise ValueError("Missing API key")

    # Prefix the model with provider if it's openrouter or others that litellm expects
    if provider == "openrouter" and not model.startswith("openrouter/"):
        model = f"openrouter/{model}"

    kwargs = {"model": model}

    if provider == "openai":
        os.environ["OPENAI_API_KEY"] = api_key
    elif provider == "anthropic":
        os.environ["ANTHROPIC_API_KEY"] = api_key
    elif provider == "openrouter":
        os.environ["OPENROUTER_API_KEY"] = api_key

    return kwargs

def generate_comment(observations: str, personality: str) -> str:
    """Generates a blurt from the axolotl based on recent observations."""
    config = load_config()
    try:
        kwargs = _get_api_kwargs()
    except ValueError:
        return "(Axolotl taps the glass...) Hey, you haven't set up your API key in config.json!"

    system_prompt = (
        f"{personality}\n\n"
        "You are observing the user's workspace. Here are the recent file events:\n"
        f"```\n{observations}\n```\n"
        "Give a short, rich, emotional response (1-2 sentences). "
        "If they are procrastinating (no recent activity), make them feel guilty or challenge them! "
        "If they are working hard (many file modifications/creations), praise them or be sarcastic about their 'dedication'. "
        "Output ONLY the raw text response."
    )

    try:
        response = litellm.completion(
            messages=[{"role": "system", "content": system_prompt}],
            max_tokens=150,
            **kwargs
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return "(Axolotl looks confused...) Something's wrong with the connection!"

def generate_choices(recent_context: str, personality: str) -> list[str]:
    """Generates 3 interactive text-RPG style choices for the user to respond to the blurt."""
    config = load_config()
    try:
        kwargs = _get_api_kwargs()
    except ValueError:
        return ["*Fix config.json*", "*Ignore axolotl*", "*Sigh*"]

    system_prompt = (
        f"{personality}\n\n"
        "Based on the following recent context/chat log, generate 3 short, text-RPG style choices (actions or dialogue) "
        "for the user to pick from. They should be emotionally engaging, funny, or play into the guilt/praise dynamic.\n"
        f"Context:\n{recent_context}\n\n"
        "Return the response ONLY as a valid JSON object with a single key 'choices' containing an array of 3 strings. Example: "
        '{"choices": ["I am working on it, promise!", "Ignore the axolotl.", "*Pat its head*"]}'
    )

    try:
        response = litellm.completion(
            messages=[{"role": "system", "content": system_prompt}],
            response_format={ "type": "json_object" } if "gpt" in kwargs["model"] else None,
            max_tokens=200,
            **kwargs
        )
        content = response.choices[0].message.content.strip()

        # Simple extraction if not returned cleanly
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        choices = json.loads(content)
        if isinstance(choices, dict) and "choices" in choices:
            choices = choices["choices"]

        if isinstance(choices, list) and len(choices) > 0:
            return [str(c) for c in choices][:3]

        return ["*Nod*", "*Ignore*", "*Sigh*"]
    except Exception as e:
        print(f"Error generating choices: {e}")
        return ["*Stare blankly*", "*Go back to work*", "*Poke axolotl*"]

def process_interaction(interaction: str, recent_context: str, personality: str) -> str:
    """Processes user interaction and generates axolotl's response, potentially updating personality."""
    config = load_config()
    from config import update_config
    try:
        kwargs = _get_api_kwargs()
    except ValueError:
        return "(Axolotl taps the glass louder...) Seriously, check config.json!"

    system_prompt = (
        f"{personality}\n\n"
        "The user just chose this action/dialogue:\n"
        f"> {interaction}\n\n"
        f"Recent context:\n{recent_context}\n\n"
        "Respond in character. Be emotional, reactive. If they chose to slack off, amplify the guilt! "
        "If they chose to work, act satisfied but demanding. Short response (1-2 sentences). "
        "Output ONLY the text."
    )

    try:
        response = litellm.completion(
            messages=[{"role": "system", "content": system_prompt}],
            max_tokens=150,
            **kwargs
        )
        ai_response = response.choices[0].message.content.strip()

        # Trigger an update of the personality based on this interaction
        update_prompt = (
            f"Current personality: {personality}\n\n"
            f"User interaction: {interaction}\n\n"
            f"AI response: {ai_response}\n\n"
            "Based on this interaction, write a slightly updated, cohesive personality description for the axolotl. "
            "Keep the core traits (cute, slightly sarcastic, demanding, emotional) but subtly shift the tone "
            "based on how the user has been acting (e.g., if they are slacking, maybe it becomes slightly more "
            "strict or disappointed; if they work, more warm or arrogant). "
            "Output ONLY the new personality text."
        )

        try:
            update_response = litellm.completion(
                messages=[{"role": "system", "content": update_prompt}],
                max_tokens=200,
                **kwargs
            )
            new_personality = update_response.choices[0].message.content.strip()
            if new_personality:
                update_config("personality", new_personality)
        except Exception:
            pass # Fails silently if it can't update personality

        return ai_response
    except Exception as e:
        return f"(Axolotl glitched...) Error: {str(e)}"
