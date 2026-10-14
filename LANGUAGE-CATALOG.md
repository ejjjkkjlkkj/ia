# Catalogue commun de langages — construction de modèles IA

Version du catalogue : 2. Les IDs sont le contrat entre `ejjjkkjlkkj/ia` et `ejjjkkjlkkj/accessibility`.

**But de ce dépôt :** utiliser ces langages pour construire le modèle IA lui-même. Un simple adaptateur, une configuration d'agent ou l'appel à un modèle externe ne satisfait pas cet objectif.

## Pistes systèmes principales

| ID | Langage | Piste de fabrication du modèle | Limite à vérifier |
|---|---|---|---|
| c | C | tenseurs CPU, opérations numériques, entraînement minimal, inférence et noyaux optimisés | allocations, stabilité numérique, bibliothèques et parallélisme |
| cpp | C++ | cœur tensoriel, autodiff, entraînement, kernels CPU/GPU et inférence | dépendances, ABI et reproductibilité |
| rust | Rust | tenseurs sûrs, autodiff, pipeline d'entraînement, checkpoints et inférence | bibliothèques numériques, SIMD/GPU et mémoire |
| zig | Zig | cœur numérique, allocations explicites, entraînement CPU et inférence | maturité des bibliothèques et accélérateurs |
| ada | Ada | tenseurs et entraînement numérique typé, tests de précision | écosystème ML et performances |
| asm-x86_64 | x86-64 Assembly | kernels bas niveau de tenseurs et opérations vectorisées utilisés par le cœur | composant d'optimisation, pas modèle complet autonome |
| asm-aarch64 | AArch64 Assembly | kernels SIMD/NEON et primitives numériques | composant d'optimisation, pas modèle complet autonome |
| asm-riscv64 | RISC-V Assembly | primitives numériques et extensions vectorielles lorsque disponibles | composant d'optimisation, dépend du matériel |
| go | Go | tenseurs, pipeline d'entraînement CPU, sérialisation et inférence | maturité des bibliothèques numériques |
| d | D | cœur numérique, entraînement CPU, gestion des données et inférence | dépendances/runtime et précision |
| nim | Nim | implémentation du modèle, boucle d'entraînement et inférence, avec inspection du code généré | dépendances et reproductibilité |
| swift | Swift | tenseurs, modèle et entraînement via outils/bibliothèques compatibles | portabilité hors plateformes prises en charge |
| pascal | Free Pascal / Object Pascal | tenseurs CPU, modèle minimal, entraînement et checkpoints | bibliothèques numériques et performances |
| odin | Odin | cœur numérique explicite, boucle d'entraînement et inférence | écosystème ML et accélération |
| fortran | Fortran | kernels numériques, tenseurs et opérations d'entraînement | couches de modèle, données et écosystème |
| csharp | C# | modèle, tenseurs, entraînement et inférence via implémentation .NET | runtime et dépendances nécessaires |
| objc | Objective-C | implémentation et intégration du modèle sur les cibles prises en charge | dépendance éventuelle aux frameworks de plateforme |

## Candidats à prouver avant d'annoncer une piste complète

| ID | Langage | Première preuve exigée |
|---|---|---|
| v | V | opérations numériques, tests de précision et entraînement miniature |
| crystal | Crystal | faisabilité runtime/GC, tenseurs et entraînement miniature |
| modula2 | Modula-2 | compilateur maintenu, opérations numériques et checkpoint |
| cobol | COBOL | cas concret et prototype numérique entraînable, sans piste fictive |
| pli | PL/I | compilateur disponible, tenseurs et test d'entraînement reproductible |

## Langages hébergés et spécifiques à une plateforme

| ID | Langage | Piste de fabrication du modèle | Limite à vérifier |
|---|---|---|---|
| java | Java | tenseurs, entraînement, checkpoints et inférence dans l'écosystème JVM | coût du runtime et bibliothèques retenues |
| kotlin | Kotlin | modèle et pipeline d'entraînement sur JVM, avec tests propres | dépendances et portabilité |
| python | Python | référence expérimentale du modèle, entraînement, évaluation et outillage de corpus | runtime hébergé; ne pas le présenter comme freestanding |
| javascript | JavaScript | modèle numérique et entraînement CPU/plateforme pris en charge | mémoire, performances et environnement |
| typescript | TypeScript | modèle numérique, entraînement et tests avec sortie JavaScript vérifiée | types effacés à l'exécution; limites de runtime |

## Contrat obligatoire de chaque piste

Chaque langage doit progressivement fournir :
- une implémentation versionnée de tenseurs et d'opérations;
- une implémentation du modèle causal minimal, pas seulement une liaison à un modèle externe;
- une boucle d'entraînement capable de produire des poids;
- la sauvegarde et le rechargement de checkpoints;
- une commande d'inférence qui charge les poids réellement produits;
- des tests numériques partagés et une comparaison de tolérance avec la référence;
- un entraînement reproductible sur données synthétiques ou licenciées, avec séparation train/validation/test;
- journaux, configuration, version de compilateur/runtime, empreinte des artefacts, mesures mémoire/temps et résultats;
- un statut indépendant : `NOT_IMPLEMENTED`, `PARTIAL`, `BLOCKED`, `NOT_VALIDATED` ou `PASS`.

## Règles de preuve

- « Le code compile » ne signifie pas « le modèle a été entraîné ».
- « L'entraînement démarre » ne signifie pas « il se termine ».
- « Un checkpoint existe » ne prouve pas une qualité utile : l'évaluation sur des données tenues à l'écart est obligatoire.
- Le partage d'un format de poids est permis; prétendre que des poids externes sont un modèle fabriqué ici ne l'est pas.
- Les pistes assembleur fournissent des noyaux bas niveau mesurables et ne sont pas présentées comme des applications complètes indépendantes.
- Les bibliothèques et runtimes peuvent être utilisés et déclarés; le cœur du modèle et son pipeline doivent rester inspectables et testés dans la piste du langage.
- Données, licences, ressources de calcul et limites de chaque langage doivent être documentées.

## Synchronisation

La liste canonique de l'accessibilité se trouve dans `ejjjkkjlkkj/accessibility` :
- `docs/LANGUAGE_CARTOGRAPHY_SCREENREADER_UEFI_OS.md`
- `docs/EXECUTION_PLAN_ALL_LANGUAGE_RELEASE_GATES.md`
- `projects/manifest.json`

Toute modification du catalogue doit garder les IDs synchronisés entre les deux dépôts. Les statuts IA et accessibilité restent indépendants.
