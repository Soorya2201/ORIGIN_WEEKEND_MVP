#!/usr/bin/env python3
"""
Test Gemini extraction directly with your lab image.
This test doesn't require the database to be running.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_gemini_extraction():
    """Test Gemini extraction directly."""
    
    print("🧪 Testing Gemini Lab Extraction")
    print("=" * 50)
    
    # Check if lab image exists
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
        print("❌ Lab image not found. Please add your lab image to tests/fixtures/")
        return False
    
    print(f"✅ Lab image found: {lab_image_path}")
    
    # Check Gemini API key
    if not os.getenv("GEMINI_API_KEY"):
        print("❌ GEMINI_API_KEY not found in environment")
        return False
    
    print("✅ Gemini API key found")
    
    # Determine MIME type
    mime_type = "image/jpeg"
    if lab_image_path.suffix.lower() == ".png":
        mime_type = "image/png"
    elif lab_image_path.suffix.lower() == ".pdf":
        mime_type = "application/pdf"
    
    print(f"📄 File type: {mime_type}")
    
    try:
        # Import and test Gemini extraction
        from app.insights.clients import extract_labs_from_media
        
        print("🔍 Extracting lab data with Gemini...")
        
        # Read the file
        with open(lab_image_path, "rb") as f:
            file_bytes = f.read()
        
        print(f"📊 File size: {len(file_bytes)} bytes")
        
        # Extract labs
        result = extract_labs_from_media(file_bytes, mime_type)
        
        print("✅ Extraction successful!")
        print(f"📋 Extracted {len(result.get('labs', []))} lab results")
        
        # Print the results
        labs = result.get('labs', [])
        for i, lab in enumerate(labs, 1):
            print(f"\n   Lab {i}:")
            print(f"     Analyte: {lab.get('analyte', 'Unknown')}")
            print(f"     Value: {lab.get('value', 'N/A')}")
            print(f"     Unit: {lab.get('unit', 'N/A')}")
            print(f"     Date: {lab.get('observed_at', 'N/A')}")
            if lab.get('ref_low') or lab.get('ref_high'):
                print(f"     Reference: {lab.get('ref_low', 'N/A')} - {lab.get('ref_high', 'N/A')}")
        
        # Print notes if any
        if result.get('notes'):
            print(f"\n📝 Notes: {result['notes']}")
        
        # Print confidence
        if result.get('confidence'):
            print(f"🎯 Confidence: {result['confidence']}")
        
        print("\n🎉 Gemini extraction test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Extraction failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_gemini_extraction()
    exit(0 if success else 1)
