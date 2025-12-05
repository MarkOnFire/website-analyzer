"""Plugin discovery and loading system.

Scans the plugins package for classes implementing the TestPlugin protocol.
"""

import importlib
import inspect
import pkgutil
import sys
from pathlib import Path
from typing import Iterator, List, Type

from pydantic import BaseModel # Moved from inside function

from src.analyzer.test_plugin import TestPlugin


def load_plugins(package_name: str = "src.analyzer.plugins") -> List[TestPlugin]:
    """Discover and instantiate test plugins from the specified package.

    Scans all modules in the package. Finds classes that:
    1. Are defined in that module (not imported)
    2. Implement the TestPlugin protocol (checked via instantiation and isinstance)
    
    Args:
        package_name: Dot-separated package path to scan.

    Returns:
        List of instantiated TestPlugin objects.
    """
    plugins: List[TestPlugin] = []

    # Ensure the current working directory is in sys.path so we can import local modules
    cwd = str(Path.cwd())
    if cwd not in sys.path:
        sys.path.insert(0, cwd)

    try:
        package = importlib.import_module(package_name)
    except ImportError:
        # If package doesn't exist, return empty list
        return []

    if not hasattr(package, "__path__"):
        return []

    for _, name, _ in pkgutil.iter_modules(package.__path__):
        full_name = f"{package_name}.{name}"
        try:
            module = importlib.import_module(full_name)
            
            for _, obj in inspect.getmembers(module, inspect.isclass):
                # Skip classes imported from elsewhere
                if obj.__module__ != full_name:
                    continue
                
                # Skip abstract classes or protocols themselves if they slip in
                if inspect.isabstract(obj):
                    continue

                # Skip Pydantic BaseModel subclasses from being treated as plugins
                if issubclass(obj, BaseModel) and obj is not BaseModel:
                    continue

                # Try to instantiate and check protocol adherence
                try:
                    # Assume plugins have no-arg constructors
                    instance = obj()
                    if isinstance(instance, TestPlugin):
                        plugins.append(instance)
                except TypeError as e:
                    # Constructor might require args, or other instantiation issue
                    pass
                except Exception as e:
                    # Other instantiation failed
                    pass

        except ImportError as e:
            continue
        except Exception as e:
            continue

    return plugins