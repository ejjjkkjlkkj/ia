# Windows quick start

## Requirements

- Windows 10 or Windows 11, x64.
- Python 3.11 or newer.
- No pip packages, cloud account, API key, GPU, or network connection is required after downloading the source archive.

Open PowerShell in this folder. If Windows blocks locally downloaded scripts, unblock this file once with:

```powershell
Unblock-File .\Start-IA.ps1
```

Run the local demonstration:

```powershell
.\Start-IA.ps1 -Mode Demo
```

Run the repository tests:

```powershell
.\Start-IA.ps1 -Mode Verify
```

## Train your own tiny checkpoint

Provide a UTF-8 text corpus (maximum 10,000 bytes for this experimental model):

```powershell
.\Start-IA.ps1 -Mode Train -TrainingCorpus .\training.txt -Checkpoint .\model.json -Epochs 1 -Seed 7 -LearningRate 0.05 -EmbeddingDim 4
```

Evaluate against a distinct UTF-8 held-out corpus. The evaluator checks that the supplied training file matches the SHA-256 embedded in the checkpoint and refuses exact training/held-out reuse:

```powershell
.\Start-IA.ps1 -Mode Evaluate -Checkpoint .\model.json -TrainingCorpus .\training.txt -HeldoutCorpus .\heldout.txt -Report .\evaluation.json
```

Generate a short sample:

```powershell
.\Start-IA.ps1 -Mode Generate -Checkpoint .\model.json -Prompt "Bonjour : "
```

The default demo stores its temporary model and reports in the Windows temporary directory. Training and evaluation files are never uploaded by this launcher.

## Scope and limitations

This package runs a small, locally trained byte-level neural predictor. It is an experimental CPU reference, **not** a production LLM or Transformer. Its short text generations may be incoherent; perplexity is a byte-level metric, not a measure of semantic correctness. The evaluator checks exact corpus identity only, not partial overlap, licensing, or representativeness.

The broader universal-model, multimodal-generation, native screen-reader, NEXORA production compiler, and cross-language checkpoint goals are not delivered by this Windows prototype. Their status remains partial or unvalidated until independently implemented and tested.
