# IA de référence pour la déficience visuelle et la cécité — contrat et feuille de route

**Statut global : PARTIAL / NOT_VALIDATED.** Ce document définit le périmètre et les preuves exigées. Il ne prétend pas que les adaptateurs, le lecteur d'écran complet, la synthèse vocale, le braille ou le matériel UEFI sont déjà fonctionnels.

## Mission produit

Construire une IA locale, utilisable hors ligne, conçue avec les personnes aveugles et malvoyantes, qui devienne une référence de qualité pour l'accessibilité numérique. La qualité doit être démontrée par l'utilisabilité, l'exactitude, la latence, la confidentialité et la compatibilité réelle — pas par des promesses ou par le seul nombre de fonctions.

L'IA complète les technologies d'assistance ; elle ne doit pas être requise pour les fonctions essentielles du lecteur d'écran. La navigation, la lecture du focus, les commandes clavier, les alertes de sécurité et les réglages doivent continuer à fonctionner sans modèle, réseau ou clé API.

## Priorités fonctionnelles

1. **Lecteur d'écran clavier-first** : lecture du focus, nom, rôle, valeur, état, raccourcis, titres, liens, listes, tableaux, formulaires, dialogues, notifications et changements dynamiques. Parcours et commandes entièrement utilisables au clavier.
2. **Adaptateurs natifs et séparés** :
   - Windows : client Microsoft UI Automation, avec gestion explicite des limites des applications et des contrôles personnalisés.
   - Linux : adaptateur AT-SPI/ATK selon le bureau et les toolkits disponibles.
   - Web : sémantique HTML native en premier, puis WAI-ARIA selon les spécifications et pratiques W3C.
   - Android, macOS, iOS et autres cibles : statut indépendant par plateforme ; aucune compatibilité ne doit être inférée d'une autre plateforme.
3. **Voix** : moteur vocal local remplaçable, interruption immédiate, priorité des annonces, prononciation multilingue, débit/volume/intonation réglables et absence de chevauchement non contrôlé. Toute voix ou donnée vocale doit avoir une licence vérifiée.
4. **Braille** : prise en charge documentée des afficheurs compatibles, tables de traduction versionnées, saisie braille si prise en charge, états de connexion et tests sur appareils réels.
5. **Compréhension assistée par IA** : expliquer une interface, résumer une page ou un document, décrire une image fournie, lire des tableaux/code et aider à accomplir une tâche. Toute inférence doit être distinguée des données accessibles réellement exposées par la plateforme. Signaler l'incertitude ; ne jamais inventer le texte d'un contrôle.
6. **Images et documents** : OCR et vision comme aides complémentaires, jamais comme substitut silencieux à l'arbre d'accessibilité. Distinguer texte extrait, description inférée et contenu vérifié.
7. **UEFI / bare metal** : piste distincte, sans dépendance obligatoire à Windows/Linux/NVDA/JAWS ou au cloud. Le rendu framebuffer, le pilote audio, la synthèse vocale et les commandes firmware doivent être marqués NOT_VALIDATED jusqu'à des essais matériels appropriés.
8. **Confidentialité et sécurité** : fonctionnement local par défaut, aucune transmission silencieuse, aucun stockage inutile des contenus lus, commandes destructives soumises à confirmation explicite et modes accessibles de récupération.
9. **Internationalisation** : français en priorité pour les essais utilisateurs initiaux, puis langues supplémentaires avec dictionnaires, prononciation et tables braille versionnés.

## Contrat commun d'accessibilité

Chaque élément accessible doit, quand la plateforme le fournit, conserver :
- identifiant et parenté dans l'arbre ;
- nom accessible, rôle, description, valeur et état ;
- focus, focusable, activé/désactivé, sélectionné, coché, développé/réduit, lecture seule et requis, selon les propriétés réellement prises en charge ;
- actions disponibles et raccourcis clavier ;
- ordre de navigation et événements de changement ;
- origine, horodatage et niveau de confiance des informations ;
- erreur explicite si une propriété est absente, obsolète ou inaccessible.

Ne pas inventer les propriétés absentes. Ne pas assimiler visibilité visuelle, présence dans l'arbre d'accessibilité et focus clavier. Éviter les annonces répétitives ; permettre de les interrompre et de les répéter. Maintenir des commandes cohérentes, configurables et sans conflit avec les applications.

## Architecture proposée

- **Core déterministe** : modèle d'élément, événements, focus, navigation, commandes et file d'annonces, testables sans IA.
- **Interfaces de plateforme** : adaptateurs séparés avec capacités déclarées, versions et tests spécifiques.
- **Sorties** : voix, braille, affichage accessible et journaux de diagnostic expurgés.
- **Service IA local facultatif** : résumé, description et aide contextuelle par interface typée, délais bornés, limites d'entrée/sortie et gestion des erreurs.
- **Contrat interopérable** : schéma versionné et vecteurs de test communs ; les implémentations dans différents langages doivent réussir les mêmes cas de conformité avant d'être considérées interopérables.
- **Mode secours** : commandes clavier essentielles et lecture basique disponibles quand le modèle, la voix avancée ou l'adaptateur IA échoue.

## Tests obligatoires

### Tests automatisés
- noms accessibles vides, noms en doublon et rôles/états contradictoires ;
- focus perdu, focus déplacé, contrôles désactivés, éléments supprimés et événements en double ;
- ordre de navigation stable, navigation clavier seule et raccourcis sans conflit ;
- contenu dynamique, tableaux, formulaires, dialogues, erreurs et notifications ;
- textes Unicode, français avec accents, ponctuation, nombres, URL, code et changement de langue ;
- lecteur vocal interrompu, file saturée, absence de périphérique audio et panne du moteur vocal ;
- déconnexion braille et périphérique non pris en charge ;
- timeout, données malformées, contenu hostile et réponse IA incorrecte ;
- mode sans réseau, sans modèle, sans clé API et sans sortie audio.

### Tests avec technologies d'assistance et utilisateurs
- NVDA et JAWS sur Windows, Narrator lorsque disponible ;
- Orca sur Linux avec les environnements pris en charge ;
- essais clavier uniquement et essais avec personnes aveugles/malvoyantes ;
- latence mesurée entre événement et annonce, précision du nom/rôle/état, répétitions et annonces manquantes ;
- essais réels de la voix et du braille sur matériel identifié ;
- UEFI et audio matériel testés séparément des émulateurs.

Les résultats doivent préciser OS/version, application, lecteur d'écran/version, périphérique, commande, journal expurgé et limites. Une simulation, un test unitaire ou un succès QEMU ne prouve pas le fonctionnement sur matériel physique.

## Critères de statut

- `NOT_IMPLEMENTED` : aucune implémentation.
- `PARTIAL` : une partie seulement est présente.
- `BLOCKED` : obstacle concret documenté.
- `NOT_VALIDATED` : code présent mais preuve d'exécution insuffisante.
- `PASS` : critères annoncés réussis avec commandes, versions, logs et résultats reproductibles.
- Les tests automatisés, essais utilisateurs, voix réelle, braille réel, UEFI et matériel physique sont des dimensions de preuve distinctes.

## Jalons

1. Stabiliser le schéma commun et les vecteurs de conformité.
2. Auditer le dépôt `ejjjkkjlkkj/accessibility` et aligner les contrats sans dupliquer les implémentations.
3. Livrer et tester le cœur déterministe clavier-first.
4. Valider un adaptateur Windows UI Automation, puis un adaptateur Linux AT-SPI avec des critères séparés.
5. Valider les annonces vocales locales et la gestion des interruptions.
6. Ajouter braille, documents, images et assistance IA comme modules explicites.
7. Faire les tests avec utilisateurs et publier des rapports de limites reproductibles.
8. Développer la piste UEFI séparément et ne la déclarer fonctionnelle qu'après validation matérielle.
9. Étendre les langages et plateformes selon le contrat commun, sans attribuer PASS à une piste non testée.

## Références techniques officielles

- W3C WAI-ARIA : https://www.w3.org/WAI/standards-guidelines/aria/
- W3C Accessible Name and Description Practices : https://www.w3.org/WAI/ARIA/apg/practices/names-and-descriptions/
- Microsoft UI Automation overview : https://learn.microsoft.com/en-us/windows/win32/winauto/uiauto-uiautomationoverview
- Microsoft UI Automation providers : https://learn.microsoft.com/en-us/windows/win32/winauto/uiauto-providersoverview
- GNOME AT-SPI developer documentation : https://gnome.pages.gitlab.gnome.org/at-spi2-core/devel-docs/index.html

Ces références guident les adaptateurs ; elles ne remplacent pas les tests d'interopérabilité avec les lecteurs d'écran réels.
