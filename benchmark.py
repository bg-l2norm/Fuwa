import time
import asyncio
from textual.app import App
from fuwa import FuwaApp
from textual.widgets import Button

async def run_benchmark():
    app = FuwaApp()

    async with app.run_test() as pilot:
        # Measure update_choices time
        start_time = time.perf_counter()
        for _ in range(1000):
            app.update_choices(["A", "B", "C"])
        end_time = time.perf_counter()

        baseline_time = end_time - start_time
        print(f"Optimized update_choices (1000 iterations): {baseline_time:.4f} seconds")

        # Measure disable_buttons time
        start_time = time.perf_counter()
        for _ in range(1000):
            app.disable_buttons()
        end_time = time.perf_counter()

        baseline_disable_time = end_time - start_time
        print(f"Optimized disable_buttons (1000 iterations): {baseline_disable_time:.4f} seconds")

if __name__ == "__main__":
    asyncio.run(run_benchmark())
