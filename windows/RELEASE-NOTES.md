# IA Windows standalone prototype

This release packages the repository's local experimental tiny neural byte predictor with a PowerShell launcher.

## Requirements
- Windows 10/11 x64
- Python 3.11+
- No third-party Python packages or API keys

## Start
Run `windows\\Start-IA.ps1 -Mode Demo` in PowerShell.
Run `windows\\Start-IA.ps1 -Mode Verify` to compile the Python source and run unit tests.

## Limitations
This is not a production LLM or Transformer. It does not deliver the repository's complete universal model, multimodal image/video generation, native screen reader, or production NEXORA compiler. Those features remain partial or unvalidated. The release is a usable Windows prototype, not completion of the entire product vision.
