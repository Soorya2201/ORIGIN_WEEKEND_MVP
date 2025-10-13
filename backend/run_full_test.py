#!/usr/bin/env python3
"""
Script to run the full integration test with real lab image and Gemini API.

Usage:
    python run_full_test.py

Requirements:
    1. Lab image at: tests/fixtures/sample_lab_results.jpg
    2. GEMINI_API_KEY in environment
    3. Database running (use: make up)
"""

import os
import sys
import subprocess
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def check_requirements():
    """Check if all requirements are met."""
    print("🔍 Checking requirements...")
    
    # Check lab image (try different formats)
    lab_image_paths = [
        Path("tests/fixtures/sample_lab_results.jpg"),
        Path("tests/fixtures/sample_lab_results.png"),
        Path("tests/fixtures/sample_lab_results.pdf")
    ]
    
    lab_image_path = None
    for path in lab_image_paths:
        if path.exists():
            lab_image_path = path
            break
    
    if not lab_image_path:
        print(f"❌ Lab image not found. Tried: {[str(p) for p in lab_image_paths]}")
        print("   Please add your lab image to tests/fixtures/ as sample_lab_results.jpg/png/pdf")
        return False
    print(f"✅ Lab image found: {lab_image_path}")
    
    # Check Gemini API key
    if not os.getenv("GEMINI_API_KEY"):
        print("❌ GEMINI_API_KEY not found in environment")
        print("   Please set your Gemini API key in .env file")
        return False
    print("✅ Gemini API key found")
    
    # Check if database is running
    try:
        result = subprocess.run(
            ["docker", "compose", "ps", "postgres"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if "Up" not in result.stdout:
            print("❌ PostgreSQL database not running")
            print("   Please run: make up")
            return False
        print("✅ PostgreSQL database is running")
    except Exception as e:
        print(f"⚠️  Could not check database status: {e}")
        print("   Make sure Docker is running and try: make up")
    
    return True

def run_test():
    """Run the full integration test."""
    print("\n🚀 Running full integration test...")
    
    # Run the test
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/integration/test_full_flow.py::test_full_lab_processing_flow",
        "-v", "-s", "--tb=short"
    ]
    
    try:
        result = subprocess.run(cmd, timeout=300)  # 5 minute timeout
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print("❌ Test timed out after 5 minutes")
        return False
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

def main():
    """Main function."""
    print("🧪 Lab Backend Full Integration Test")
    print("=" * 50)
    
    if not check_requirements():
        print("\n❌ Requirements not met. Please fix the issues above.")
        sys.exit(1)
    
    print("\n✅ All requirements met!")
    
    if run_test():
        print("\n🎉 Full integration test completed successfully!")
        print("   The lab processing pipeline is working end-to-end!")
    else:
        print("\n❌ Full integration test failed.")
        print("   Check the output above for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()
