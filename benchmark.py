import time
from infrastructure.config import load_config

start = time.perf_counter()
for _ in range(10000):
    load_config()
end = time.perf_counter()
print(f"Post-optimization: {end - start:.4f} seconds")
