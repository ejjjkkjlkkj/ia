# NEXORA IA Windows prototype release

This release provides a portable source ZIP for Windows 10/11 x64 and a PowerShell launcher.

## Start
1. Extract the ZIP.
2. Install Python 3.12 or newer.
3. Open PowerShell in the extracted folder.
4. Run `windows\\Start-IA.ps1 -Mode Demo`.

To run the complete test suite, install pytest with `py -3 -m pip install pytest`, then run `windows\\Start-IA.ps1 -Mode Verify`.

## Available local modes
- `Demo`: train a small synthetic byte-level model, verify its held-out corpus, and generate a short sample.
- `Train`: train a checkpoint from a UTF-8 corpus.
- `Evaluate`: evaluate a checkpoint against a distinct held-out corpus.
- `Generate`: generate a short byte-level sample from a checkpoint.
- `Verify`: compile Python sources and run pytest.

## Limits
This is a source package, not a standalone executable or installer. The neural baseline is experimental, not a production LLM/Transformer. Full universal-model training, production multimodal generation, native screen reader and UEFI capabilities remain partial or unvalidated.
