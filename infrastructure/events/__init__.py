import inspect
import asyncio
import threading
import queue

class EventBus:
    def __init__(self):
        self._subscribers = {}
        self._queue = queue.Queue()
        self._worker_thread = threading.Thread(target=self._worker, daemon=True)
        self._worker_thread.start()

    def subscribe(self, event_type: str, callback):
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)

    def publish(self, event_type: str, **kwargs):
        self._queue.put((event_type, kwargs))

    def _worker(self):
        while True:
            event_type, kwargs = self._queue.get()
            if event_type in self._subscribers:
                for callback in self._subscribers[event_type]:
                    try:
                        if inspect.iscoroutinefunction(callback):
                            try:
                                loop = asyncio.get_running_loop()
                                loop.create_task(callback(**kwargs))
                            except RuntimeError:
                                asyncio.run(callback(**kwargs))
                        else:
                            callback(**kwargs)
                    except Exception as e:
                        print(f"EventBus callback error: {e}")
            self._queue.task_done()
