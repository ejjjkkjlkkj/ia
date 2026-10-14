# NEXORA — spécification initiale du langage universel

**Statut : prototype d'interpréteur PARTIAL. Aucun compilateur de production, backend OS/UEFI ou ABI stable n'est revendiqué.**

## Objectif

NEXORA est le nom de travail du langage universel du projet. Il vise une syntaxe source commune pour les applications, outils IA, accessibilité, systèmes et logiciels portables. Il ne remplace pas les langages existants : il doit pouvoir les interopérer via des interfaces explicites et des backends, plutôt que prétendre qu'un unique langage peut déjà compiler parfaitement tous les programmes de tous les langages.

NEXORA est distinct du langage existant **U** (ulanguage.org). U reste une piste du catalogue; il n'est pas le nom du nouveau langage.

## Principes

1. **Spécification avant les backends** : grammaire versionnée, types, erreurs, règles de mémoire, modules et ABI.
2. **Unicode/UTF-8** : identifiants Unicode acceptés par le prototype; la normalisation Unicode et les règles exactes d'identifiants doivent être figées dans une future version.
3. **IR portable** : la cible prévue est une représentation intermédiaire versionnée, indépendante de l'OS, puis des backends distincts (C, LLVM ou WebAssembly après preuve de faisabilité).
4. **Interopérabilité** : FFI et génération de bindings explicites pour C/Rust/Go/etc.; ne pas promettre une conversion sans perte du code source arbitraire.
5. **Sécurité** : pas d'exécution de commandes système implicite, pas d'accès arbitraire au réseau ou au firmware par défaut; capacités et permissions explicites.
6. **Accessibilité native** : API sémantique commune pour rôles, états, focus, événements clavier et annonces vocales, sans faire dépendre le cœur du langage d'un modèle IA.
7. **IA** : l'intégration au modèle universel du dépôt est optionnelle et passe par une interface versionnée; le langage et son compilateur doivent rester utilisables sans cloud.
8. **UEFI/bare metal** : cible expérimentale distincte avec contraintes de mémoire, allocateur, ABI, pilotes et services disponibles. Pas de promesse de support UEFI tant qu'un binaire EFI n'a pas été compilé et exécuté avec preuves séparées.
9. **Reproductibilité** : tests de conformité, fixtures d'entrée/sortie, diagnostics stables, hashes et versions d'outils.
10. **Pas de revendications abusives** : support d'Unicode ne signifie pas compréhension sémantique; parseur fonctionnel ne signifie pas compilateur complet.

## Syntaxe du prototype

```nexora
# commentaires sur une ligne
let café = "Bonjour 世界";
let calcul = 2 + 3 * 4;
print(café);
print(calcul);
```

Le prototype actuel prend en charge : entiers, chaînes, booléens, identifiants Unicode, déclarations `let`, `print(...)`, parenthèses, arithmétique + - * /, commentaires `#` et `//`. Il utilise un interpréteur de référence Python pour tester la syntaxe et la sémantique initiales. Il n'a pas encore de fonctions, modules, boucles, types statiques, gestion mémoire spécifiée, compilateur ou runtime autonome.

## Architecture cible

- Frontend : lexer, parseur, AST, diagnostics.
- Sémantique : types, portée, modules, règles de mutation et gestion des erreurs.
- IR : format canonique versionné avec tests de sérialisation.
- Backend hôte : commencer par une sortie de référence testable (bytecode/VM ou C).
- Backends ultérieurs : WebAssembly, Linux/macOS/Windows et UEFI, chacun avec des tests et limites propres.
- Outils : formatter, analyseur statique, test runner, gestionnaire de paquets et documentation.
- Conformité : corpus de programmes valides/invalides, résultats attendus et exécution déterministe.

## Portes de validation

- **L0 — Lexer/parser** : PASS si tests syntaxiques et diagnostics passent.
- **L1 — Sémantique** : variables, portée, types et erreurs testés.
- **L2 — IR** : format stable, versionné et round-trip.
- **L3 — Backend** : code généré compilé et exécuté sur les cibles déclarées.
- **L4 — Interop** : tests ABI/FFI sur chaque paire prise en charge.
- **L5 — OS** : tests réels ou CI sur OS indiqués.
- **L6 — UEFI** : binaire EFI et test d'émulation étiqueté séparément de la preuve sur matériel.
- **L7 — Sécurité/accessibilité** : tests de permissions, clavier, arbre sémantique et lecteur d'écran.

Aucune porte n'est validée par simple présence d'un dossier ou d'un README.
