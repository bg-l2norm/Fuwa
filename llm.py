import json
import litellm
import os
from config import load_config
from axolotl import AxolotlAnimation

def _get_api_kwargs():
    config = load_config()
    model = config.get("model", "gpt-4o-mini")
    provider = config.get("provider", "openai")
    api_key = config.get("api_key", "")

    # Prefix the model with provider if it's openrouter or others that litellm expects
    if provider == "openrouter" and not model.startswith("openrouter/"):
        model = f"openrouter/{model}"

    kwargs = {"model": model}

    if api_key:
        if provider == "openai":
            os.environ["OPENAI_API_KEY"] = api_key
        elif provider == "anthropic":
            os.environ["ANTHROPIC_API_KEY"] = api_key
        elif provider == "openrouter":
            os.environ["OPENROUTER_API_KEY"] = api_key

    return kwargs

def summarize_file(filename: str, content: str) -> str:
    """Generates a high-level summary of a file's contents to capture intent/emotion."""
    kwargs = _get_api_kwargs()

    system_prompt = (
        "You are an AI assistant that summarizes codebase files to capture the user's "
        "high-level intent and emotional state. You don't care about specific code syntax "
        "or minor details. Just give a brief (1-3 sentences) description of what the file "
        "is about, and what the user is likely trying to achieve. Keep it very short."
    )

    user_message = f"File: {filename}\nContent:\n```\n{content}\n```"

    try:
        response = litellm.completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            max_tokens=100,
            **kwargs
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error summarizing file: {e}")
        return "Failed to summarize file."


def generate_comment(observations: str, personality: str, file_memories: str = "") -> str:
    """Generates a blurt from the axolotl based on recent observations and memories."""
    kwargs = _get_api_kwargs()

    available_moods = AxolotlAnimation.get_available_moods()
    moods_str = ", ".join(f"[MOOD: {m}]" for m in available_moods)

    system_prompt = (
        f"{personality}\n\n"
        "You are observing the user's workspace.\n"
        "Give a short, rich, emotional response (1-2 sentences). "
        "If they are procrastinating (no recent activity), make them feel guilty or challenge them! "
        "If they are working hard (many file modifications/creations), praise them or be sarcastic about their 'dedication'. "
        f"Include a mood tag at the VERY BEGINNING of your response. Valid tags: {moods_str}. "
        f"For example: '{moods_str.split(', ')[0]} Wow, you are working so hard!' "
        "Output ONLY the raw text response."
    )

    user_message = f"Here are the recent file events:\n```\n{observations}\n```\n\n"
    if file_memories:
        user_message += f"Here are summaries of some of the files for context:\n```\n{file_memories}\n```"

    try:
        response = litellm.completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            max_tokens=150,
            **kwargs
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"(Axolotl looks confused...) Error: {str(e)}"

def generate_choices(recent_context: str, personality: str) -> list[str]:
    """Generates 3 interactive text-RPG style choices for the user to respond to the blurt."""
    kwargs = _get_api_kwargs()

    system_prompt = (
        f"{personality}\n\n"
        "Based on the recent context/chat log, generate 3 short, text-RPG style choices (actions or dialogue) "
        "for the user to pick from. They should be emotionally engaging, funny, or play into the guilt/praise dynamic.\n"
        "Return the response ONLY as a valid JSON object with a single key 'choices' containing an array of 3 strings. Example: "
        '{"choices": ["I am working on it, promise!", "Ignore the axolotl.", "*Pat its head*"]}'
    )

    user_message = f"Context:\n{recent_context}"

    try:
        response = litellm.completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
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
    kwargs = _get_api_kwargs()
    from config import update_config

    available_moods = AxolotlAnimation.get_available_moods()
    moods_str = ", ".join(f"[MOOD: {m}]" for m in available_moods)

    system_prompt = (
        f"{personality}\n\n"
        "Respond in character to the user's action/dialogue. Be emotional, reactive. If they chose to slack off, amplify the guilt! "
        "If they chose to work, act satisfied but demanding. Short response (1-2 sentences). "
        f"Include a mood tag at the VERY BEGINNING of your response. Valid tags: {moods_str}. "
        f"For example: '{moods_str.split(', ')[-1] if ',' in moods_str else moods_str.split(', ')[0]} Do not ignore me!' "
        "Output ONLY the text."
    )

    user_message = (
        "The user just chose this action/dialogue:\n"
        f"> {interaction}\n\n"
        f"Recent context:\n{recent_context}"
    )

    try:
        response = litellm.completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            max_tokens=150,
            **kwargs
        )
        ai_response = response.choices[0].message.content.strip()

        # Trigger an update of the personality based on this interaction
        update_prompt = (
            f"Current personality: {personality}\n\n"
            "Based on this interaction, write a slightly updated, cohesive personality description for the axolotl. "
            "Keep the core traits (cute, slightly sarcastic, demanding, emotional) but subtly shift the tone "
            "based on how the user has been acting (e.g., if they are slacking, maybe it becomes slightly more "
            "strict or disappointed; if they work, more warm or arrogant). "
            "Output ONLY the new personality text."
        )

        update_user_message = (
            f"User interaction: {interaction}\n\n"
            f"AI response: {ai_response}"
        )

        try:
            update_response = litellm.completion(
                messages=[
                    {"role": "system", "content": update_prompt},
                    {"role": "user", "content": update_user_message}
                ],
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
