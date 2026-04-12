import importlib
import pkgutil
import commands

def discover():
    """Scan the commands/ directory. Each sub-module that exposes a `handle`
    function is registered under its directory name."""
    registry = {}
    for importer, name, _ in pkgutil.iter_modules(commands.__path__):
        try:
            module = importlib.import_module(f"commands.{name}")
            if hasattr(module, "handle"):
                registry[name] = module.handle
        except Exception as e:
            pass
    return registry
