#!/usr/bin/env python3
"""Test VOICEVOX connection and synthesis."""

import asyncio
import sys


async def test_voicevox(host: str = "localhost", port: int = 50021) -> bool:
    """Test VOICEVOX connection.

    Args:
        host: VOICEVOX host address.
        port: VOICEVOX port number.

    Returns:
        True if test passed.
    """
    print(f"Testing VOICEVOX at {host}:{port}")
    print("=" * 40)

    try:
        from src.tts.voicevox import VoicevoxEngine
    except ImportError:
        print("✗ Could not import VoicevoxEngine")
        print("  Make sure you're in the project directory")
        return False

    engine = VoicevoxEngine(host=host, port=port)

    # Test 1: Check availability
    print("\n1. Checking connection...")
    if await engine.is_available():
        print("   ✓ VOICEVOX is running")
    else:
        print("   ✗ VOICEVOX is not available")
        print("   Make sure VOICEVOX is running")
        return False

    # Test 2: Get version
    print("\n2. Getting version...")
    version = await engine.get_version()
    if version:
        print(f"   ✓ Version: {version}")
    else:
        print("   ✗ Could not get version")

    # Test 3: Get speakers
    print("\n3. Getting speakers...")
    speakers = await engine.get_speakers()
    if speakers:
        print(f"   ✓ Found {len(speakers)} speakers")
        print("   Available speakers:")
        for s in speakers[:5]:  # Show first 5
            print(f"     - ID {s.id}: {s.name}")
        if len(speakers) > 5:
            print(f"     ... and {len(speakers) - 5} more")
    else:
        print("   ✗ No speakers found")
        return False

    # Test 4: Synthesize test audio
    print("\n4. Testing synthesis...")
    try:
        audio = await engine.synthesize("テスト", speaker_id=1)
        if audio and len(audio.data) > 0:
            print(f"   ✓ Synthesized {len(audio.data)} bytes")
        else:
            print("   ✗ Synthesis returned empty data")
            return False
    except Exception as e:
        print(f"   ✗ Synthesis failed: {e}")
        return False

    await engine.close()

    print("\n" + "=" * 40)
    print("All tests passed! ✓")
    return True


def main() -> int:
    """Run VOICEVOX test."""
    import argparse

    parser = argparse.ArgumentParser(description="Test VOICEVOX connection")
    parser.add_argument("--host", default="localhost", help="VOICEVOX host")
    parser.add_argument("--port", type=int, default=50021, help="VOICEVOX port")
    args = parser.parse_args()

    result = asyncio.run(test_voicevox(args.host, args.port))
    return 0 if result else 1


if __name__ == "__main__":
    sys.exit(main())
