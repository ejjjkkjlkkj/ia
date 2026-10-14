# Piste de modèle IA — K

**Statut initial : `NOT_IMPLEMENTED`**  
**Priorité proposée : Piste numérique expérimentale**

## Objectif

Calcul compact sur tableaux et données; prototype expérimental.

Cette piste doit contenir du code source écrit dans K qui implémente réellement le modèle et son apprentissage. Un adaptateur vers un modèle pré-entraîné externe ne suffit pas.

## Étapes de réalisation

1. Identifier et figer la version du compilateur/interpréteur et les dépendances nécessaires.
2. Ajouter des opérations numériques avec tests de précision.
3. Implémenter un modèle miniature avec paramètres entraînables dans K.
4. Préparer des données synthétiques ou licenciées avec séparation entraînement/validation/test.
5. Exécuter un entraînement reproductible et enregistrer la configuration et les métriques.
6. Sauvegarder les poids, calculer leur SHA-256, puis recharger le checkpoint.
7. Vérifier l'inférence à partir des poids rechargés et tester les résultats sur des données tenues à l'écart.
8. Mesurer temps, mémoire et limites; joindre les journaux exacts.

## Risques et limites à valider

Écosystème et accès aux outils peuvent être limités; préciser implémentation/licence.

## Statut de preuve

- Source du modèle : **NOT_IMPLEMENTED**
- Compilation/exécution réelle : **NOT_VALIDATED**
- Entraînement terminé : **NOT_IMPLEMENTED**
- Checkpoint rechargé et inférence : **NOT_VALIDATED**
- Benchmarks : **NOT_VALIDATED**

Ne passer à `PASS` qu'après avoir exécuté et conservé les preuves correspondantes. La présence de ce fichier ne constitue pas une validation.
