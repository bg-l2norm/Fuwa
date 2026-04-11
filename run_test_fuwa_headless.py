import asyncio
from fuwa import FuwaApp

async def run_test():
    app = FuwaApp()
    async with app.run_test() as pilot:
        print("App is running:", app.is_running)
        app.log_message("Test", "Hello World")
        print("App log added")

asyncio.run(run_test())
