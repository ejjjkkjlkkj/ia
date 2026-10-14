# Index des modèles IA par langage

Objectif : un répertoire et une piste de modèle distincts par langage, et non un unique modèle externe enveloppé par des adaptateurs.

Chaque dossier doit progressivement contenir le code du modèle, le pipeline d'entraînement, les tests, la sauvegarde/relecture des poids, l'inférence et les preuves. Les assembleurs fournissent des noyaux bas niveau pour un modèle hôte; Scratch vise un modèle pédagogique à petite échelle.

## Pistes
- [`models/c/`](models/c/README.md) — **C** : Tenseurs FP32, entraînement causal CPU, checkpoints et inférence.
- [`models/cpp/`](models/cpp/README.md) — **C++** : Tenseurs, gradients, entraînement, sérialisation et inférence.
- [`models/rust/`](models/rust/README.md) — **Rust** : Tenseurs sûrs, gradients, boucle d'entraînement et checkpoints.
- [`models/go/`](models/go/README.md) — **Go** : Opérations numériques, entraînement CPU, checkpoints et inférence.
- [`models/d/`](models/d/README.md) — **D** : Cœur numérique, entraînement et inférence avec tests de précision.
- [`models/zig/`](models/zig/README.md) — **Zig** : Tenseurs, allocation explicite, entraînement CPU et inférence.
- [`models/ada/`](models/ada/README.md) — **Ada** : Tenseurs typés, apprentissage miniature et validation.
- [`models/nim/`](models/nim/README.md) — **Nim** : Code d'entraînement, inspection du code généré et tests.
- [`models/swift/`](models/swift/README.md) — **Swift** : Calcul tensoriel, entraînement et inférence sur cible prise en charge.
- [`models/pascal/`](models/pascal/README.md) — **Free Pascal / Object Pascal** : Opérations numériques, entraînement miniature et checkpoints.
- [`models/odin/`](models/odin/README.md) — **Odin** : Calcul tensoriel explicite et entraînement CPU.
- [`models/fortran/`](models/fortran/README.md) — **Fortran** : Primitives numériques, couches et entraînement.
- [`models/csharp/`](models/csharp/README.md) — **C#** : Tenseurs, entraînement, sauvegarde et inférence .NET.
- [`models/objc/`](models/objc/README.md) — **Objective-C** : Implémentation numérique et intégration de plateforme déclarée.
- [`models/asm-x86_64/`](models/asm-x86_64/README.md) — **Assembleur x86-64** : Noyaux numériques bas niveau mesurés; dépend d'un modèle hôte complet.
- [`models/asm-aarch64/`](models/asm-aarch64/README.md) — **Assembleur AArch64** : Noyaux numériques SIMD/NEON comparés à la référence.
- [`models/asm-riscv64/`](models/asm-riscv64/README.md) — **Assembleur RISC-V 64** : Noyaux numériques adaptés aux extensions disponibles.
- [`models/v/`](models/v/README.md) — **V** : Prototype de tenseurs et entraînement; valider compilateur et runtime.
- [`models/crystal/`](models/crystal/README.md) — **Crystal** : Prototype du modèle et de l'entraînement; évaluer GC et coûts runtime.
- [`models/modula2/`](models/modula2/README.md) — **Modula-2** : Prototype après validation du compilateur et de la cible.
- [`models/cobol/`](models/cobol/README.md) — **COBOL** : Piste expérimentale : démontrer un modèle numérique entraînable.
- [`models/pli/`](models/pli/README.md) — **PL/I** : Piste expérimentale : vérifier compilateur, opérations et entraînement.
- [`models/java/`](models/java/README.md) — **Java** : Modèle JVM : tenseurs, entraînement, checkpoints et inférence.
- [`models/kotlin/`](models/kotlin/README.md) — **Kotlin** : Modèle Kotlin/JVM : pipeline d'entraînement et inférence.
- [`models/python/`](models/python/README.md) — **Python** : Implémentation expérimentale de référence, entraînement et évaluation.
- [`models/javascript/`](models/javascript/README.md) — **JavaScript** : Calcul numérique et entraînement selon le runtime.
- [`models/typescript/`](models/typescript/README.md) — **TypeScript** : Calcul numérique et entraînement testés à l'exécution.
- [`models/scratch/`](models/scratch/README.md) — **Scratch** : Petit modèle pédagogique par blocs, données synthétiques et apprentissage démontrable; pas un LLM géant.

## Contrat
- [ ] Code source du modèle dans le langage du dossier.
- [ ] Tests numériques et entraînement reproductible.
- [ ] Entraînement réellement exécuté sur données synthétiques/licenciées.
- [ ] Checkpoint créé, hash enregistré, puis rechargé.
- [ ] Inférence du checkpoint rechargé vérifiée.
- [ ] Mesures et limites consignées dans `STATUS.md`.

Statuts : `NOT_IMPLEMENTED`, `PARTIAL`, `BLOCKED`, `NOT_VALIDATED`, `PASS`. Un dossier ou une spécification n'est pas une preuve de modèle entraîné.
