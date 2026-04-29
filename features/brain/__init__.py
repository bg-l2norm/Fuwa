import os
import time
import collections
from infrastructure.llm import generate_comment, generate_choices, process_interaction, summarize_files_batch
from infrastructure.memory import get_all_memories, search_memory, update_memory, update_memories
from infrastructure.config import load_config, save_config, update_config

class FuwaBrain:
    def __init__(self, event_bus):
        self.bus = event_bus
        self.config = load_config()
        self.chat_history = []
        self.initial_choice_made = False
        self.choice_clicks = 0
        self.heartbeat_count = 0
        self.session_start_time = time.time()
        self.is_first_heartbeat = True
        self.unlock_task = None
        self.mood_reset_task = None

        self.cpu_history = collections.deque(maxlen=15)
        self.mem_history = collections.deque(maxlen=15)

        # Subscriptions
        self.bus.subscribe("heartbeat_tick", self.on_heartbeat_tick)
        self.bus.subscribe("user_chat", self.on_user_chat)
        self.bus.subscribe("app_start", self.on_app_start)
        self.bus.subscribe("config_updated", self.on_config_updated)

    def _get_llm_kwargs(self):
        return {
            "provider": self.config.get("provider", "openai"),
            "model": self.config.get("model", "gpt-4o-mini"),
            "api_key": self.config.get("api_key", ""),
        }

    def on_config_updated(self, config):
        self.config = config

    def extract_and_set_mood(self, text: str) -> str:
        import re
        match = re.search(r"\[MOOD:\s*([a-zA-Z0-9_,\s]+)\]", text, re.IGNORECASE)
        if match:
            moods = [m.strip().upper() for m in match.group(1).split(",")]
            if moods:
                self.bus.publish("mood_set", mood=moods[0])
                
                # We need a timer to reset mood
                import threading
                def reset_mood_timer():
                    time.sleep(5.0)
                    self.bus.publish("mood_set", mood="NORMAL")
                t = threading.Thread(target=reset_mood_timer, daemon=True)
                t.start()
            text = re.sub(r"\[MOOD:\s*[a-zA-Z0-9_,\s]+\]\s*", "", text, flags=re.IGNORECASE).strip()
        return text

    def on_app_start(self):
        self.bus.publish("log_message", sender="System", message="Fuwa woke up!")
        self.bus.publish("choices_update", choices=["*Stare blankly*", "*Go back to work*", "*Poke axolotl*"])

    def on_heartbeat_tick(self, events):
        """Processes events from the observer via heartbeat tick."""
        is_startup = self.is_first_heartbeat
        if is_startup:
            self.is_first_heartbeat = False

        if not events and not is_startup:
            self._update_stats()
            return

        needs_unlock = (self.choice_clicks >= 2)
        self.choice_clicks = 0

        if needs_unlock:
            self._unlock_choices()

        # Format events
        obs_str = ""
        if events:
            obs_lines = [f"{e['action'].upper()}: {e['absolute_path']}" for e in events]
            obs_str = "\n".join(obs_lines)

        personality = self.config.get("personality", "")
        llm_kwargs = self._get_llm_kwargs()

        # Summarize files modified
        files_to_summarize = []
        for event in events:
            if event["action"] in ("modified", "created"):
                filepath = event["absolute_path"]
                if os.path.isfile(filepath):
                    try:
                        with open(filepath, "r", encoding="utf-8") as f:
                            content = f.read(1500)
                        files_to_summarize.append({"filename": event["filename"], "content": content})
                    except Exception:
                        pass
        
        if files_to_summarize:
            try:
                summaries = summarize_files_batch(files_to_summarize, **llm_kwargs)
                if summaries:
                    update_memories(summaries)
                    self.bus.publish("memory_updated")
            except Exception as e:
                pass

        if self.initial_choice_made or is_startup:
            self.bus.publish("disable_choices", message="Thinking...")

        query_text = " ".join([e["filename"] for e in events]) if events else "project"
        memories = search_memory(query_text, top_k=5)

        # Get available moods to explicitly pass from logic to UI? We shouldn't rely on AxolotlAnimation here directly.
        # Actually Brain orchestrates it. Let's pass common moods.
        available_moods = ["NORMAL", "HAPPY", "SAD", "ANGRY", "SLEEPY", "EXCITED", "QUESTIONING", "CONFUSED", "SPARKLE", "HEARTS"]

        if is_startup:
            self.initial_choice_made = True
            system_prompt = "System: The application has just started. Proactively greet the user and set yourself up!"
            if memories:
                system_prompt += f"\nInitial memories of the project:\n{memories}"
            
            ai_response, mem_updates, new_personality = process_interaction(
                interaction=system_prompt,
                recent_context=obs_str,
                personality=personality,
                available_moods=available_moods,
                is_startup=True,
                **llm_kwargs
            )
            comment = ai_response
        else:
            comment = generate_comment(
                observations=obs_str,
                personality=personality,
                available_moods=available_moods,
                file_memories=str(memories),
                **llm_kwargs
            )

        comment = self.extract_and_set_mood(comment)
        self.bus.publish("log_message", sender="Fuwa", message=comment)

        self.chat_history.append(f"Fuwa: {comment}")
        if len(self.chat_history) > 20:
            self.chat_history.pop(0)

        context = "\n".join(self.chat_history[-5:])

        if self.initial_choice_made:
            choices = generate_choices(context, personality, **llm_kwargs)
            self.bus.publish("choices_update", choices=choices)

        self.heartbeat_count += 1
        self._update_stats()

    def _unlock_choices(self):
        personality = self.config.get("personality", "")
        context = "\n".join(self.chat_history[-5:])
        choices = generate_choices(context, personality, **self._get_llm_kwargs())
        self.bus.publish("choices_update", choices=choices)

    def on_user_chat(self, user_choice: str):
        self.bus.publish("disable_choices", message="Thinking...")
        self.initial_choice_made = True
        self.choice_clicks += 1

        personality = self.config.get("personality", "")
        context = "\n".join(self.chat_history[-5:])
        llm_kwargs = self._get_llm_kwargs()
        available_moods = ["NORMAL", "HAPPY", "SAD", "ANGRY", "SLEEPY", "EXCITED", "QUESTIONING", "CONFUSED", "SPARKLE", "HEARTS"]

        ai_response, mem_updates, new_personality = process_interaction(
            interaction=user_choice,
            recent_context=context,
            personality=personality,
            available_moods=available_moods,
            **llm_kwargs
        )
        
        if mem_updates:
            update_memories(mem_updates)
        if new_personality:
            update_config("personality", new_personality)
            self.config["personality"] = new_personality

        response_clean = self.extract_and_set_mood(ai_response)
        self.bus.publish("log_message", sender="Fuwa", message=response_clean)

        self.chat_history.append(f"You: {user_choice}")
        self.chat_history.append(f"Fuwa: {response_clean}")
        if len(self.chat_history) > 20:
            self.chat_history = self.chat_history[-20:]

        if self.choice_clicks >= 2:
            self.bus.publish("disable_choices", message="Get back to work!")
            self.bus.publish("log_message", sender="System", message="Fuwa is watching you. Go write some code!")
            # Start unlock timer
            import threading
            def unlock_timer():
                time.sleep(120.0)
                self.choice_clicks = 0
                self._unlock_choices()
            t = threading.Thread(target=unlock_timer, daemon=True)
            t.start()
        else:
            new_context = "\n".join(self.chat_history[-5:])
            choices = generate_choices(new_context, personality, **llm_kwargs)
            self.bus.publish("choices_update", choices=choices)

    def _update_stats(self):
        active_time = int(time.time() - self.session_start_time)
        import resource
        mem_usage_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        mem_usage_mb = mem_usage_kb / 1024.0

        cpu_val = 0.0
        try:
            load1, _, _ = os.getloadavg()
            cpu_count = os.cpu_count() or 1
            cpu_val = min(100.0, (load1 / cpu_count) * 100.0)
        except Exception:
            pass

        self.bus.publish(
            "dashboard_stats", 
            active_time=active_time,
            mem_usage_mb=mem_usage_mb,
            cpu_val=cpu_val,
            heartbeat_count=self.heartbeat_count,
            chat_length=len(self.chat_history)
        )
