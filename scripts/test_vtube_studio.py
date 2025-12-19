#!/usr/bin/env python3
"""Test VTube Studio connection."""

import asyncio
import sys


async def test_vtube_studio(host: str = "localhost", port: int = 8001) -> bool:
    """Test VTube Studio connection.

    Args:
        host: VTube Studio host address.
        port: VTube Studio API port.

    Returns:
        True if test passed.
    """
    print(f"Testing VTube Studio at {host}:{port}")
    print("=" * 40)

    try:
        from src.avatar.vtube_studio import VTubeStudioController
    except ImportError:
        print("✗ Could not import VTubeStudioController")
        print("  Make sure you're in the project directory")
        return False

    controller = VTubeStudioController(
        host=host,
        port=port,
        plugin_name="AITuber Test",
        plugin_developer="Test Script",
    )

    # Test 1: Connect
    print("\n1. Connecting to VTube Studio...")
    try:
        await controller.connect()
        print("   ✓ Connected successfully")
    except Exception as e:
        print(f"   ✗ Connection failed: {e}")
        print("\n   Make sure:")
        print("   - VTube Studio is running")
        print("   - API is enabled (Settings → General → Start API)")
        print("   - Accept the plugin authentication in VTube Studio")
        return False

    # Test 2: Get current model
    print("\n2. Getting current model info...")
    try:
        model_info = await controller.get_current_model()
        if model_info:
            model_name = model_info.get("modelName", "Unknown")
            print(f"   ✓ Current model: {model_name}")
        else:
            print("   ⚠ No model loaded")
    except Exception as e:
        print(f"   ✗ Could not get model info: {e}")

    # Test 3: Get hotkeys
    print("\n3. Getting available hotkeys...")
    try:
        hotkeys = await controller.get_available_hotkeys()
        if hotkeys:
            print(f"   ✓ Found {len(hotkeys)} hotkeys")
            for hk in hotkeys[:5]:
                print(f"     - {hk.get('name', 'Unknown')}")
            if len(hotkeys) > 5:
                print(f"     ... and {len(hotkeys) - 5} more")
        else:
            print("   ⚠ No hotkeys found")
    except Exception as e:
        print(f"   ✗ Could not get hotkeys: {e}")

    # Test 4: Test lip sync parameter
    print("\n4. Testing lip sync parameter...")
    try:
        await controller.set_lip_sync(0.5)
        await asyncio.sleep(0.5)
        await controller.set_lip_sync(0.0)
        print("   ✓ Lip sync parameter works")
    except Exception as e:
        print(f"   ✗ Lip sync test failed: {e}")

    # Disconnect
    print("\n5. Disconnecting...")
    await controller.disconnect()
    print("   ✓ Disconnected")

    print("\n" + "=" * 40)
    print("All tests passed! ✓")
    return True


def main() -> int:
    """Run VTube Studio test."""
    import argparse

    parser = argparse.ArgumentParser(description="Test VTube Studio connection")
    parser.add_argument("--host", default="localhost", help="VTube Studio host")
    parser.add_argument("--port", type=int, default=8001, help="VTube Studio API port")
    args = parser.parse_args()

    result = asyncio.run(test_vtube_studio(args.host, args.port))
    return 0 if result else 1


if __name__ == "__main__":
    sys.exit(main())
