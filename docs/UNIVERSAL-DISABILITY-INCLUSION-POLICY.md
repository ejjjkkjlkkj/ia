# Politique d'inclusion universelle — NEXORA IA

**Objectif : zéro discrimination dans la conception, l'accès et l'usage.** L'IA doit être conçue avec les personnes handicapées et tenir compte de la diversité des handicaps, des besoins variables, des handicaps multiples et des situations temporaires. « Zéro discrimination » est un objectif de conception et de contrôle continu, pas une conformité que l'on peut déclarer sans preuves.

## Périmètre universel

Le produit doit couvrir, sans hiérarchie entre les personnes :

- **Vision** : cécité, basse vision, daltonisme, sensibilité à la lumière ; lecteur d'écran, braille, grossissement, contraste, alternatives textuelles et descriptions d'images.
- **Audition** : surdité, malentendance et acouphènes ; sous-titres, transcriptions, alertes visuelles/haptiques et contrôle du son.
- **Mobilité et motricité** : commandes clavier seules, navigation sans glisser-déposer, compatibilité avec contacteurs, commandes vocales et technologies de pointage adaptées lorsqu'elles sont prises en charge ; cibles utilisables et absence d'actions exigeant une précision fine.
- **Parole et communication** : saisie alternative, communication augmentée et alternative (CAA/AAC), entrées non vocales et sorties pouvant être lues ou copiées.
- **Cognition, apprentissage et neurodivergence** : langage clair, étapes explicites, structure prévisible, possibilité de simplifier ou détailler, aide mémoire, erreurs compréhensibles et réduction des distractions.
- **Santé mentale, fatigue, douleur et maladies chroniques** : pauses, reprise, absence de pression temporelle injustifiée, réglages de stimulation et possibilité de différer une tâche.
- **Handicaps multiples, fluctuants, invisibles ou temporaires** : profils combinables, réglages indépendants et adaptation sans exiger une étiquette médicale.

Cette liste est un minimum de conception, pas une taxonomie exhaustive ni une supposition sur les capacités d'une personne.

## Principes obligatoires

1. **Égalité d'accès** : aucune fonctionnalité essentielle ne doit être réservée à un seul mode sensoriel ou moteur lorsque des alternatives raisonnables sont possibles.
2. **Choix individuel** : chaque personne peut configurer les modalités, le niveau de détail, le rythme et les aides ; ne pas déduire un diagnostic à partir de son comportement.
3. **Aucun diagnostic requis** : les préférences d'accessibilité doivent pouvoir être activées sans divulguer de diagnostic ou de justificatif.
4. **Multimodalité équivalente** : information critique disponible par plusieurs canaux adaptés ; ne pas dépendre uniquement du son, de la couleur, du mouvement, de la voix ou de la vision.
5. **Clavier et commandes alternatives** : toutes les fonctions essentielles doivent être accessibles sans souris et sans geste précis ; ne pas imposer la voix.
6. **Langage compréhensible** : proposer une explication simple, une version détaillée et des étapes actionnables sans retirer l'information nécessaire.
7. **Prévisibilité et contrôle** : éviter les limites de temps évitables, les changements de contexte inattendus, les animations non essentielles et la perte de progression.
8. **Interopérabilité** : utiliser les API d'accessibilité natives et les formats ouverts pertinents ; déclarer les limites par système, application et appareil.
9. **Vie privée et sécurité** : minimiser les données ; aucun profil médical inféré ou transmis silencieusement ; confirmation accessible avant une action destructive.
10. **Co-conception rémunérée et respectueuse** : inclure des personnes aux handicaps variés dans la recherche, les tests et la gouvernance ; ne pas les traiter comme un groupe homogène.
11. **Accessibilité du développement** : documentation, installation, configuration, support, consentement, signalement de bugs et processus de mise à jour doivent eux-mêmes être accessibles.
12. **Pas de promesse sans preuve** : documenter les fonctions implémentées, les essais et les limites. Une checklist ou un score automatique ne suffit pas à prouver l'expérience réelle.

## Exigences produit transversales

- Paramètres persistants et faciles à retrouver : contraste, taille, espacement, réduction du mouvement, durée/rythme, niveau de détail, langue, voix, sous-titres, annonces, navigation et aides d'entrée.
- Plusieurs sorties : texte accessible, synthèse vocale quand disponible, braille quand compatible, sous-titres/transcriptions et signaux visuels/haptiques quand pris en charge.
- Plusieurs entrées : clavier, pointeur, contacteur, dictée et CAA lorsque disponibles ; aucune entrée unique ne doit être obligatoire pour les tâches essentielles.
- Gestion de panne : retour accessible si un moteur IA, un périphérique, le réseau ou un module d'assistance échoue.
- Documents et médias : structure sémantique, alternatives textuelles, transcriptions, sous-titres et distinction entre contenu observé et interprétation générée.
- IA sûre : signaler l'incertitude, permettre de corriger ou désactiver l'assistance, ne pas inventer les états d'interface ni prendre des décisions médicales ou administratives au nom de l'utilisateur.
- Pas de mode « handicap » unique : les préférences sont combinables et peuvent changer dans le temps.
- Tests de régression d'accessibilité dans chaque changement de code, avec rapport des régressions et blocage des changements qui cassent un parcours essentiel déjà validé.

## Mesure et validation

Les résultats doivent être ventilés par fonctionnalité et contexte d'usage, sans prétendre qu'une personne représente tout un handicap. Tester notamment :
- parcours essentiels au clavier seul et avec entrées alternatives ;
- lecteurs d'écran, grossissement, contraste et braille sur configurations réelles ;
- sous-titres, transcriptions, alertes sans audio et alternatives à la voix ;
- langage clair, charge cognitive, interruptions, erreurs et reprise après pause ;
- handicaps combinés et réglages contradictoires ;
- mode hors ligne, panne d'appareil, faible débit et absence de compte ;
- installation, onboarding, récupération, confidentialité, sécurité et assistance ;
- tests automatisés, tests manuels par spécialistes et essais utilisateurs avec consentement.

Chaque rapport indique la version testée, la plateforme, les aides techniques, le parcours, les résultats, les limites et les problèmes connus. Un résultat automatisé ne remplace pas l'évaluation par des utilisateurs. Ne pas publier de statistiques ou de scores non mesurés.

## Statuts de preuve

- `NOT_IMPLEMENTED` : aucune implémentation.
- `PARTIAL` : couverture incomplète.
- `BLOCKED` : obstacle identifié.
- `NOT_VALIDATED` : preuve insuffisante.
- `PASS` : critères définis réussis avec résultats reproductibles et limites publiées.

**Statut initial : PARTIAL / NOT_VALIDATED.** Ce contrat définit l'exigence produit ; il ne signifie pas que toutes les aides ou plateformes sont déjà implémentées ou validées.

## Références de départ

- W3C Web Accessibility Initiative (WAI) : https://www.w3.org/WAI/
- W3C Web Content Accessibility Guidelines (WCAG) : https://www.w3.org/WAI/standards-guidelines/wcag/
- W3C WAI-ARIA : https://www.w3.org/WAI/standards-guidelines/aria/
- Microsoft UI Automation : https://learn.microsoft.com/en-us/windows/win32/winauto/uiauto-uiautomationoverview
- GNOME AT-SPI : https://gnome.pages.gitlab.gnome.org/at-spi2-core/devel-docs/index.html
