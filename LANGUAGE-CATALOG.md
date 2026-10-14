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


## Piste supplémentaire : Scratch

| ID | Langage | Piste de fabrication du modèle | Limite à vérifier |
|---|---|---|---|
| scratch | Scratch | Petit modèle pédagogique construit par blocs, avec poids explicites et apprentissage démontrable | Ne pas prétendre qu'un projet Scratch entraîne un grand modèle de langage; documenter taille, opérations et limites |

Les dossiers d'implémentation individuels se trouvent dans `models/<id>/`. Voir [MODELS-INDEX.md](MODELS-INDEX.md). Chaque dossier commence en `NOT_IMPLEMENTED` tant qu'aucune implémentation et aucun entraînement ne sont prouvés.


## Piste supplémentaire : U

| ID | Langage | Piste de fabrication du modèle | Limite à vérifier |
|---|---|---|---|
| u | U (ulanguage.org) | Prototype de calcul tensoriel, modèle miniature entraînable, checkpoints et inférence dans le langage U | Vérifier le compilateur/version, la syntaxe réellement supportée et la chaîne U → C avant toute déclaration de compilation; le code généré en C ne remplace pas les sources U du modèle |

Référence de langage retenue : [spécification U](https://ulanguage.org/u_language). D'autres projets utilisent également le nom « U »; cette piste désigne explicitement le langage documenté par ulanguage.org.


## Langages supplémentaires retenus après recherche

| ID | Langage | Priorité | Piste proposée | Limite à vérifier |
|---|---|---|---|---|
| julia | Julia | Priorité élevée | Tenseurs, différentiation automatique, entraînement et inférence; excellent candidat pour prototyper le modèle lui-même. | Confirmer dépendances, reproductibilité des paquets et export des poids. |
| mojo | Mojo | Priorité élevée | Modèle et noyaux numériques CPU/GPU; langage conçu pour l’infrastructure IA. | La prise en charge Windows native est limitée; validation possible sous WSL/Linux et selon matériel. |
| chapel | Chapel | Priorité moyenne | Calcul parallèle, entraînement expérimental et opérations distribuées. | Écosystème IA moins mature; démontrer un modèle autonome plutôt qu’un pilote de bibliothèques. |
| r | R | Priorité moyenne | Modèles statistiques, prototypes d’apprentissage, évaluation et analyses de données. | Moins adapté au cœur bas niveau/UEFI; documenter runtime et dépendances. |
| apl | APL | Piste numérique expérimentale | Opérations sur tableaux et prototype de petit modèle entraînable. | Syntaxe et écosystème spécialisés; choisir un interpréteur précis et vérifier les performances. |
| j | J | Piste numérique expérimentale | Calcul sur tableaux, prototype numérique et expérimentation concise. | Valider autodiff, gestion des poids et entraînement reproductible. |
| k | K | Piste numérique expérimentale | Calcul compact sur tableaux et données; prototype expérimental. | Écosystème et accès aux outils peuvent être limités; préciser implémentation/licence. |
| q | q | Piste spécialisée | Calcul tabulaire et séries temporelles; modèle miniature sur données numériques. | Écosystème associé à kdb+; vérifier licence, disponibilité et portabilité avant de s’engager. |
| lua | Lua | Priorité moyenne | Modèle léger, moteur d’inférence embarqué ou orchestration; possibilité d’implémenter un petit modèle natif. | Écosystème moderne d’entraînement plus restreint; ne pas confondre intégration d’un moteur externe et modèle écrit en Lua. |

Les priorités sont des choix de planification, pas des preuves de compilation ou d'entraînement. Les pistes APL/J/K/q sont exploratoires et ne doivent pas être annoncées comme modèles fonctionnels sans tests concrets.
