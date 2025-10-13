# Test Fixtures

This directory contains test fixtures for the lab backend integration tests.

## Required Files

### `sample_lab_results.jpg`
- **Purpose**: Real lab result image for full integration testing
- **Format**: JPEG, PNG, or PDF
- **Content**: Should contain lab results with analytes, values, units, and dates
- **Size**: Recommended under 10MB for testing

## How to Add Your Lab Image

1. **Get a lab result image/PDF** from your medical records or a sample lab report
2. **Save it as** `sample_lab_results.jpg` (or `.png`, `.pdf`)
3. **Place it in this directory**: `tests/fixtures/sample_lab_results.jpg`
4. **Run the full test**: `make test-full` or `python run_full_test.py`

## Example Lab Results to Look For

The test works best with lab results containing:
- **LDL Cholesterol** (mg/dL)
- **HbA1c** (%)
- **TSH** (mIU/L)
- **Ferritin** (ng/mL)
- **Other common lab values**

## Privacy Note

- **Remove any personal information** before adding the image
- **Use de-identified lab results** only
- **The system will redact PII** automatically, but it's better to start clean

## Running the Full Test

```bash
# Make sure database is running
make up

# Run the full integration test
make test-full

# Or run directly
python run_full_test.py
```

The test will:
1. ✅ Upload your lab image
2. 🔍 Extract lab data using Gemini AI
3. 🧠 Generate clinical insights using rules
4. 📊 Store results in database
5. 📝 Generate LLM summary
6. 🎉 Verify the complete pipeline works
