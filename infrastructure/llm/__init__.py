import json
import os
import urllib.request
import re
import urllib.error

def simple_completion(messages, model, provider, api_key, max_tokens=100, response_format=None):
    if provider in ["openai", "openrouter"]:
        url = "https://api.openai.com/v1/chat/completions" if provider == "openai" else "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://github.com/fuwa-app/fuwa",
            "X-Title": "Fuwa"
        }
        data = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens
        }
        if response_format:
            data["response_format"] = response_format

        req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode("utf-8"))
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                return content if content is not None else ""
        except urllib.error.HTTPError as e:
            raise Exception(f"HTTP Error {e.code}: {e.read().decode('utf-8')}")

    elif provider == "anthropic":
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        system_msg = ""
        anthropic_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_msg += msg["content"] + "\n"
            else:
                anthropic_messages.append({"role": msg["role"], "content": msg["content"]})

        data = {
            "model": model,
            "messages": anthropic_messages,
            "max_tokens": max_tokens
        }
        if system_msg:
            data["system"] = system_msg.strip()

        req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode("utf-8"))
                content = result.get("content", [{}])[0].get("text", "")
                return content if content is not None else ""
        except urllib.error.HTTPError as e:
            raise Exception(f"HTTP Error {e.code}: {e.read().decode('utf-8')}")

    raise Exception(f"Unsupported provider: {provider}")


def _parse_json_response(content: str) -> dict:
    content = content.strip()
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].split("```")[0].strip()
    try:
        return json.loads(content)
    except Exception as e:
        print(f"Error parsing JSON: {e}")
        return {}

def summarize_paths_batch(paths: list[str], provider: str, model: str, api_key: str) -> dict:
    """Generates high-level summaries based ONLY on file paths/names."""
    if not paths:
        return {}

    system_prompt = (
        "You are an AI assistant analyzing a project's structure. "
        "Given a list of file paths, provide a brief (1 sentence) guess of what each file is for, "
        "based purely on its name and directory structure. "
        "Return the result ONLY as a valid JSON object where keys are the file paths and values are the summaries."
    )

    paths_str = "\n".join(paths)
    user_message = f"File paths:\n{paths_str}"

    try:
        response_format = {"type": "json_object"} if "gpt" in model else None
        response = simple_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            model=model,
            provider=provider,
            api_key=api_key,
            max_tokens=1500,
            response_format=response_format
        )
        return _parse_json_response(response)
    except Exception as e:
        print(f"Error summarizing paths batch: {e}")
        return {}

def summarize_files_batch(files_data: list[dict], provider: str, model: str, api_key: str) -> dict:
    """Generates summaries for a batch of files using their partial content."""
    if not files_data:
        return {}

    system_prompt = (
        "You are an AI assistant that summarizes codebase files to capture the user's high-level intent. "
        "Given a list of files and their partial contents, provide a brief (1-3 sentences) description of what "
        "each file is about. "
        "Return the result ONLY as a valid JSON object where keys are the file paths and values are the summaries."
    )

    user_parts = []
    for fd in files_data:
        user_parts.append(f"File: {fd['filename']}\nContent:\n```\n{fd['content']}\n```\n")

    user_message = "\n".join(user_parts)

    try:
        response_format = {"type": "json_object"} if "gpt" in model else None
        response = simple_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            model=model,
            provider=provider,
            api_key=api_key,
            max_tokens=2500,
            response_format=response_format
        )
        return _parse_json_response(response)
    except Exception as e:
        print(f"Error summarizing files batch: {e}")
        return {}

def generate_comment(observations: str, personality: str, available_moods: list[str], provider: str, model: str, api_key: str, file_memories: str = "") -> str:
    """Generates a blurt from the axolotl based on recent observations and memories."""

    moods_str = ", ".join(f"[MOOD: {m}]" for m in available_moods)

    system_prompt = (
        "You are observing the user's workspace.\n"
        "Give a short, rich, emotional response (1-2 sentences). "
        "If they are procrastinating (no recent activity), make them feel guilty or challenge them! "
        "If they are working hard (many file modifications/creations), praise them or be sarcastic about their 'dedication'. "
        "Include a mood tag at the VERY BEGINNING of your response. "
        "Output ONLY the raw text response."
    )

    # Read optional SOUL.md and USER.md
    soul_content = ""
    if os.path.exists("SOUL.md"):
        try:
            with open("SOUL.md", "r", encoding="utf-8") as f:
                soul_content = f.read().strip()
        except Exception:
            pass

    user_md_content = ""
    if os.path.exists("USER.md"):
        try:
            with open("USER.md", "r", encoding="utf-8") as f:
                user_md_content = f.read().strip()
        except Exception:
            pass

    user_message = (
        f"Your personality:\n{personality}\n\n"
        f"Valid mood tags: {moods_str}. "
        f"For example: '{moods_str.split(', ')[0]} Wow, you are working so hard!'\n\n"
        f"Here are the recent file events:\n```\n{observations}\n```\n\n"
    )
    if soul_content:
        user_message += f"Your deepest behavioral instructions (SOUL):\n```\n{soul_content}\n```\n\n"
    if user_md_content:
        user_message += f"Information about the user and their intents (USER):\n```\n{user_md_content}\n```\n\n"

    if file_memories:
        user_message += f"Here are summaries of some of the files for context:\n```\n{file_memories}\n```"

    try:
        response = simple_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            model=model,
            provider=provider,
            api_key=api_key,
            max_tokens=150
        )
        return response.strip()
    except Exception as e:
        return f"(Axolotl looks confused...) Error: {str(e)}"

def generate_choices(recent_context: str, personality: str, provider: str, model: str, api_key: str) -> list[str]:
    """Generates 3 interactive text-RPG style choices for the user to respond to the blurt."""

    system_prompt = (
        "Based on the recent context/chat log, generate 3 short, text-RPG style choices (actions or dialogue) "
        "from the USER's perspective for them to respond to the companion. "
        "These are choices the USER will make. Do not make the companion talk to itself. "
        "They should be emotionally engaging, funny, or play into the guilt/praise dynamic.\n"
        "Return the response ONLY as a valid JSON object with a single key 'choices' containing an array of 3 strings. Example: "
        '{"choices": ["I am working on it, promise!", "Ignore the axolotl.", "*Pat its head*"]}'
    )

    user_message = f"Your personality:\n{personality}\n\nContext:\n{recent_context}"

    try:
        response_format = {"type": "json_object"} if "gpt" in model else None
        content = simple_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            model=model,
            provider=provider,
            api_key=api_key,
            max_tokens=200,
            response_format=response_format
        )
        content = content.strip()

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

def process_interaction(interaction: str, recent_context: str, personality: str, available_moods: list[str], provider: str, model: str, api_key: str, is_startup: bool = False) -> tuple[str, dict, str]:
    """
    Processes user interaction and generates axolotl's response.
    Returns: (ai_response, memory_updates, new_personality)
    Memory updates is a dictionary of {filename: summary}.
    New personality is a string, could be None if no update.
    """
    import subprocess

    moods_str = ", ".join(f"[MOOD: {m}]" for m in available_moods)

    system_prompt = (
        "Respond in character to the user's action/dialogue. Be emotional, reactive. If they chose to slack off, amplify the guilt! "
        "If they chose to work, act satisfied but demanding. Short response (1-2 sentences). "
        "Include a mood tag at the VERY BEGINNING of your response. "
        "Output ONLY the text. "
        "You have access to tools! "
        "If you want to read files or run read-only terminal commands (e.g. ls, cat, grep), output [RUN: command] in your response. "
        "Do NOT use pipes (|) or redirects (>) as they are not supported. "
        "If you want to write a summary to your memory, output [MEM: filename | summary] in your response. "
        "If you want to edit your persona (SOUL.md) or user preferences (USER.md), output [WRITE: filename | content] in your response. Only SOUL.md and USER.md can be written. "
        "If you use a tool, you will get the result back to formulate your next response."
    )

    # Read optional SOUL.md and USER.md
    soul_content = ""
    if os.path.exists("SOUL.md"):
        try:
            with open("SOUL.md", "r", encoding="utf-8") as f:
                soul_content = f.read().strip()
        except Exception:
            pass

    user_md_content = ""
    if os.path.exists("USER.md"):
        try:
            with open("USER.md", "r", encoding="utf-8") as f:
                user_md_content = f.read().strip()
        except Exception:
            pass

    user_message = (
        f"Your personality:\n{personality}\n\n"
        f"Valid mood tags: {moods_str}. "
        f"For example: '{moods_str.split(', ')[-1] if ',' in moods_str else moods_str.split(', ')[0]} Do not ignore me!'\n\n"
    )

    if soul_content:
        user_message += f"Your deepest behavioral instructions (SOUL):\n```\n{soul_content}\n```\n\n"
    if user_md_content:
        user_message += f"Information about the user and their intents (USER):\n```\n{user_md_content}\n```\n\n"

    if is_startup:
        bootstrap_content = ""
        if os.path.exists("BOOTSTRAP.md"):
            try:
                with open("BOOTSTRAP.md", "r", encoding="utf-8") as f:
                    bootstrap_content = f.read().strip()
            except Exception:
                pass
        if bootstrap_content:
            user_message += f"Startup Instructions (BOOTSTRAP):\n```\n{bootstrap_content}\n```\n\n"

        user_message += (
            "This is the application startup! Proceed to proactively greet the user and follow the BOOTSTRAP instructions!\n\n"
            f"Here is some initial context about the project:\n{interaction}\n\n"
            f"Recent context:\n{recent_context}"
        )
    else:
        user_message += (
            "The user just chose this action/dialogue:\n"
            f"> {interaction}\n\n"
            f"Recent context:\n{recent_context}"
        )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ]

    memory_updates = {}

    try:
        ai_response = ""
        for _ in range(3):
            ai_response = simple_completion(
                messages=messages,
                model=model,
                provider=provider,
                api_key=api_key,
                max_tokens=150
            ).strip()

            cmd_match = re.search(r'\[RUN:\s*(.*?)\]', ai_response)
            mem_match = re.search(r'\[MEM:\s*(.*?)\s*\|\s*(.*?)\]', ai_response)
            write_match = re.search(r'\[WRITE:\s*(.*?)\s*\|\s*(.*)\]', ai_response, re.DOTALL)

            if cmd_match:
                cmd = cmd_match.group(1)
                try:
                    # Execute read-only tools safely
                    import shlex
                    import glob
                    raw_args = shlex.split(cmd)
                    if not raw_args:
                        raise Exception("Empty command.")

                    allowed_commands = {'ls', 'cat', 'grep', 'head', 'tail', 'find', 'pwd'}
                    if raw_args[0] not in allowed_commands:
                        raise Exception(f"Command '{raw_args[0]}' is not allowed. Only read-only commands ({', '.join(allowed_commands)}) are permitted.")

                    args = []
                    for arg in raw_args:
                        expanded_arg = os.path.expanduser(os.path.expandvars(arg))
                        if any(c in expanded_arg for c in ('*', '?', '[')):
                            matches = glob.glob(expanded_arg)
                            if matches:
                                args.extend(matches)
                            else:
                                args.append(expanded_arg)
                        else:
                            args.append(expanded_arg)

                    result = subprocess.run(args, capture_output=True, text=True, timeout=5)
                    output = (result.stdout + result.stderr).strip()
                    if not output:
                        output = "Command executed with no output."
                except Exception as e:
                    output = str(e)

                messages.append({"role": "assistant", "content": ai_response})
                messages.append({"role": "user", "content": f"Output of {cmd}:\n{output[:1000]}\nNow respond to the user."})
                continue

            elif mem_match:
                key = mem_match.group(1).strip()
                val = mem_match.group(2).strip()
                memory_updates[key] = val

                messages.append({"role": "assistant", "content": ai_response})
                messages.append({"role": "user", "content": f"Memory updated for {key}.\nNow respond to the user."})
                continue

            elif write_match:
                filename = write_match.group(1).strip()
                content = write_match.group(2).strip()
                if content.endswith(']'):
                    content = content[:-1].strip()

                if filename in ["SOUL.md", "USER.md"]:
                    try:
                        with open(filename, "w", encoding="utf-8") as f:
                            f.write(content)
                        messages.append({"role": "assistant", "content": ai_response})
                        messages.append({"role": "user", "content": f"Successfully updated {filename}.\nNow respond to the user."})
                    except Exception as e:
                        messages.append({"role": "assistant", "content": ai_response})
                        messages.append({"role": "user", "content": f"Failed to update {filename}: {str(e)}.\nNow respond to the user."})
                else:
                    messages.append({"role": "assistant", "content": ai_response})
                    messages.append({"role": "user", "content": f"Error: You are only allowed to write to SOUL.md or USER.md. Writing to {filename} is forbidden.\nNow respond to the user."})
                continue

            break

        # Trigger an update of the personality based on this interaction
        update_prompt = (
            "Based on this interaction, write a slightly updated, cohesive personality description for the axolotl. "
            "Keep the core traits (cute, slightly sarcastic, demanding, emotional) but subtly shift the tone "
            "based on how the user has been acting (e.g., if they are slacking, maybe it becomes slightly more "
            "strict or disappointed; if they work, more warm or arrogant). "
            "Output ONLY the new personality text."
        )

        update_user_message = (
            f"Current personality: {personality}\n\n"
            f"User interaction: {interaction}\n\n"
            f"AI response: {ai_response}"
        )

        new_personality = None
        try:
            new_personality_str = simple_completion(
                messages=[
                    {"role": "system", "content": update_prompt},
                    {"role": "user", "content": update_user_message}
                ],
                model=model,
                provider=provider,
                api_key=api_key,
                max_tokens=200
            )
            new_personality_str = new_personality_str.strip()
            if new_personality_str:
                new_personality = new_personality_str
        except Exception:
            pass # Fails silently if it can't update personality

        return ai_response, memory_updates, new_personality
    except Exception as e:
        return f"(Axolotl glitched...) Error: {str(e)}", {}, None
