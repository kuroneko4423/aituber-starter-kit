#!/usr/bin/env python3
"""Check if all dependencies are properly installed."""

import sys
from importlib import import_module


def check_module(name: str, package: str | None = None) -> bool:
    """Check if a module can be imported.

    Args:
        name: Display name for the module.
        package: Package name to import (defaults to name).

    Returns:
        True if module is available.
    """
    package = package or name
    try:
        import_module(package)
        print(f"✓ {name}")
        return True
    except ImportError as e:
        print(f"✗ {name}: {e}")
        return False


def main() -> int:
    """Run dependency checks."""
    print("AITuber Starter Kit - Dependency Check")
    print("=" * 40)
    print()

    all_ok = True

    # Core dependencies
    print("Core Dependencies:")
    all_ok &= check_module("aiohttp")
    all_ok &= check_module("websockets")
    all_ok &= check_module("httpx")
    print()

    # YouTube
    print("YouTube Chat:")
    all_ok &= check_module("pytchat")
    print()

    # OpenAI
    print("OpenAI:")
    all_ok &= check_module("openai")
    print()

    # VTube Studio
    print("VTube Studio:")
    all_ok &= check_module("pyvts")
    print()

    # Audio
    print("Audio:")
    all_ok &= check_module("sounddevice")
    all_ok &= check_module("numpy")
    print()

    # Configuration
    print("Configuration:")
    all_ok &= check_module("yaml", "yaml")
    all_ok &= check_module("pydantic")
    all_ok &= check_module("pydantic-settings", "pydantic_settings")
    all_ok &= check_module("python-dotenv", "dotenv")
    print()

    # Summary
    print("=" * 40)
    if all_ok:
        print("All dependencies are installed! ✓")
        return 0
    else:
        print("Some dependencies are missing. ✗")
        print("Run: pip install -r requirements.txt")
        return 1


if __name__ == "__main__":
    sys.exit(main())
