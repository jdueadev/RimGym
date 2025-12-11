#!/usr/bin/env python3
"""Verify development environment setup.

This script checks that the RimGym development environment is properly
configured and ready for contribution.

Usage:
    python scripts/verify_setup.py
    
    # Or with uv
    uv run python scripts/verify_setup.py
"""

import subprocess
import sys
from pathlib import Path


def verify_setup():
    """Run all verification checks."""
    print("🔍 Verifying RimGym development setup...\n")
    
    checks = [
        check_python_version,
        check_imports,
        check_package_installed,
        check_tests_discoverable,
        check_uv_available,
    ]
    
    results = []
    for check in checks:
        try:
            result = check()
            results.append(result)
            status = "✓" if result else "✗"
            print(f"{status} {check.__doc__}")
        except Exception as e:
            results.append(False)
            print(f"✗ {check.__doc__}")
            print(f"  Error: {e}")
    
    print()  # Blank line before summary
    
    if all(results):
        print("✅ All checks passed! Your setup is ready.")
        print("\nNext steps:")
        print("  1. Read CONTRIBUTING.md for workflow guidelines")
        print("  2. Create a feature branch: git checkout -b feature/my-feature")
        print("  3. Make your changes and run tests: uv run pytest tests/")
        return 0
    else:
        print("❌ Some checks failed. See errors above.")
        print("\nTroubleshooting:")
        print("  - Run: cd src/RimGym && uv pip install -e .")
        print("  - Check: uv pip list | grep rimgym")
        print("  - See CONTRIBUTING.md for detailed setup instructions")
        return 1


def check_python_version():
    """Check Python version is 3.11+"""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 11:
        print(f"  Python {version.major}.{version.minor}.{version.micro}")
        return True
    print(f"  Python {version.major}.{version.minor}.{version.micro} (need 3.11+)")
    return False


def check_imports():
    """Check that rimgym imports work"""
    try:
        # Try importing core modules
        from client import SpectatorClient
        from client.connection import ConnectionManager
        print("  All core modules importable")
        return True
    except ImportError as e:
        print(f"  Import failed: {e}")
        return False


def check_package_installed():
    """Check that rimgym package is installed"""
    try:
        result = subprocess.run(
            ["uv", "pip", "list"],
            capture_output=True,
            text=True,
            check=False,
        )
        
        if result.returncode == 0:
            if "rimgym" in result.stdout.lower():
                # Extract version if possible
                for line in result.stdout.split("\n"):
                    if "rimgym" in line.lower():
                        print(f"  {line.strip()}")
                        break
                return True
            else:
                print("  Package not found in uv pip list")
                return False
        else:
            # Fallback to pip if uv fails
            result = subprocess.run(
                ["pip", "list"],
                capture_output=True,
                text=True,
                check=False,
            )
            if "rimgym" in result.stdout.lower():
                for line in result.stdout.split("\n"):
                    if "rimgym" in line.lower():
                        print(f"  {line.strip()}")
                        break
                return True
            return False
    except FileNotFoundError:
        print("  uv not found, trying pip")
        try:
            result = subprocess.run(
                ["pip", "list"],
                capture_output=True,
                text=True,
                check=False,
            )
            if "rimgym" in result.stdout.lower():
                return True
        except Exception:
            pass
        return False


def check_tests_discoverable():
    """Check that pytest can discover tests"""
    try:
        # Try to collect tests without running them
        result = subprocess.run(
            ["uv", "run", "pytest", "--collect-only", "-q"],
            capture_output=True,
            text=True,
            cwd="src/RimGym",
            check=False,
        )
        
        if result.returncode == 0:
            # Count how many tests were collected
            output = result.stdout
            if "test" in output.lower():
                # Extract test count if possible
                lines = output.strip().split("\n")
                for line in lines:
                    if "test" in line.lower():
                        print(f"  {line.strip()}")
                        break
                return True
            return False
        else:
            print(f"  pytest collection failed: {result.stderr[:100]}")
            return False
    except FileNotFoundError:
        print("  pytest not available")
        return False


def check_uv_available():
    """Check that uv package manager is available"""
    try:
        result = subprocess.run(
            ["uv", "--version"],
            capture_output=True,
            text=True,
            check=False,
        )
        
        if result.returncode == 0:
            version = result.stdout.strip()
            print(f"  {version}")
            return True
        return False
    except FileNotFoundError:
        print("  uv not found (install: curl -LsSf https://astral.sh/uv/install.sh | sh)")
        return False


def main():
    """Main entry point."""
    try:
        return verify_setup()
    except KeyboardInterrupt:
        print("\n\n⚠️  Verification interrupted by user")
        return 130


if __name__ == "__main__":
    sys.exit(main())
