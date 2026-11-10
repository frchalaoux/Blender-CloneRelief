# Clone Relief pour Blender

[Français](README.fr.md) · [English](README.md)

*La version anglaise traduit l’état actuel du projet; elle sera actualisée sur demande.*

Clone Relief est un add-on Blender expérimental qui transfère le relief d’une
zone source vers une zone cible du même maillage. Il agit sur la géométrie et
permet de régler le transfert avant de l’appliquer.

**Version :** 0.2.0 · **Blender cible :** 4.5.8 LTS · **Plateforme de référence :** macOS Intel

**Versions et tags :** [Version publiée : v0.2.0 (prototype)](https://github.com/frchalaoux/Blender-CloneRelief/releases/tag/v0.2.0) · [liste complète des tags GitHub](https://github.com/frchalaoux/Blender-CloneRelief/tags). Aucune version de développement n’est publiée pour le moment.

> Clone Relief est un prototype. Il n’est pas encore qualifié pour garantir
> qu’un maillage soit imprimable.

**Licence :** [GNU GPL version 3 ou ultérieure](LICENSE).

## Sommaire

- [Compatibilité et état](#compatibilité-et-état)
- [Installation](#installation)
- [Utilisation rapide](#utilisation-rapide)
- [Documentation spécialisée](#documentation-spécialisée)
- [Développement](#développement)
- [Limites](#limites)

## Compatibilité et état

Clone Relief vise Blender **4.5.8 LTS**. La version 0.2.0 fournit la capture
d’une zone source et d’une cible, l’aperçu, l’application annulable et la
réapplication depuis la cible capturée. Le contrôle topologique et la
localisation de composantes déconnectées ont aussi été utilisés sur un scan.
La version 0.2.0 ajoute une interface française/anglaise qui suit la langue
d’interface sélectionnée dans Blender.

L’interface de l’add-on suit la langue choisie dans Blender en français ou en
anglais. Pour le français, active **Interface** dans **Preferences → Interface
→ Translation**. Les autres langues de Blender affichent les textes anglais.

La comparaison avant/après et le parcours d’export STL restent à valider de
bout en bout. M6 s’appuie sur le 3D Print Toolbox pour les contrôles de
fabricabilité dans Blender, puis vérifie l’export dans le trancheur et par une
impression représentative. Voir le [protocole de qualification](documentation/PRINT_QUALIFICATION.md).

## Installation

### Installer la Release publiée (recommandé)

Télécharge l’[archive ZIP prête à installer Clone Relief 0.2.0](https://github.com/frchalaoux/Blender-CloneRelief/releases/download/v0.2.0/blender_clone_relief_0.2.0.zip). Garde-la au format ZIP, sans la décompresser. Pour ce parcours, tu n’as pas besoin d’installer ni de lancer Python séparément, et tu n’as pas besoin d’une copie du dépôt source. Blender exécute l’add-on avec le Python intégré à Blender; il est distinct de la commande `python3.11` du Terminal présentée plus bas.

Dans Blender 4.5.8 :

1. Ouvre **Blender → Preferences → Get Extensions**.
2. Dans le menu en haut à droite, choisis **Install from Disk…** et sélectionne le ZIP téléchargé.
3. Dans les préférences, recherche **Clone Relief** et active l’add-on.
4. Dans la vue 3D, ouvre la barre latérale avec **N**, puis choisis l’onglet **Clone Relief**.

### Construire le ZIP depuis le code source (développeurs uniquement)

Ignore cette section si tu veux seulement installer la Release publiée. Ce parcours sert aux développeurs qui reconstruisent le ZIP à partir du code source. Ici, `python3.11` désigne une installation autonome de Python 3.11 sur l’ordinateur, accessible comme commande dans le Terminal. Elle est distincte du Python intégré à Blender, même si le numéro de version est le même. Le script n’installe pas Python. Si le Terminal répond que `python3.11` est introuvable, il faut d’abord installer Python 3.11 séparément.

```bash
python3.11 scripts/build_addon_zip.py
```

Cela crée `dist/blender_clone_relief_0.2.0.zip`; la commande **n’installe pas** l’add-on dans Blender. Pour utiliser cette archive construite localement, suis ensuite les étapes Blender ci-dessus et sélectionne le ZIP dans `dist/` au lieu du fichier téléchargé depuis la Release.

L’add-on ne contient aucune bibliothèque native dépendante d’un système et
est censé fonctionner sur les plateformes prises en charge par Blender 4.5.8.
Il a seulement été testé sur macOS Intel; Windows, Linux et les Mac Apple
Silicon restent à vérifier.

Le [guide utilisateur](documentation/USER_GUIDE.md) décrit le parcours complet dans Blender.

## Utilisation rapide

Travaille sur une copie du maillage. Les captures et le transfert se font en
**Edit Mode**, sur le même objet :

1. Sélectionne les faces d’une zone source saine, puis clique **Capturer la source**.
2. Sélectionne les faces de la zone à corriger, puis clique **Capturer la cible**.
3. Clique **Prévisualiser l’effet**. Ajuste les paramètres et prévisualise à nouveau
   si nécessaire; le compte rendu apparaît sous **Prévisualiser l’effet** et
   **Appliquer le relief**.
4. Clique **Appliquer le relief**. Tu peux modifier les paramètres et réappliquer :
   chaque application repart de la géométrie enregistrée par **Capturer la cible**.
   **Undo** annule l’application.
5. Dans la section M5, contrôle la topologie et, si besoin, utilise
   **Localiser une composante…** pour sélectionner un groupe déconnecté et
   cadrer la vue dessus.

Les commandes de comparaison et d’export STL sont documentées dans le
[guide utilisateur](documentation/USER_GUIDE.md). La comparaison sert à
l’inspection; efface-la et reviens au maillage de travail avant l’export.

![Exemple synthétique : profil source, cible plane avant et relief transféré](documentation/examples/clone_relief_before_after.png)

## Documentation spécialisée

- [Guide utilisateur](documentation/USER_GUIDE.md) — installation, captures,
  réglages, application, contrôle topologique et export.
- [Spécifications](documentation/SPECIFICATIONS.md) — exigences fonctionnelles
  et critères d’acceptation.
- [Qualification pour l’impression](documentation/PRINT_QUALIFICATION.md) — contrôles et preuves à réunir pour un modèle, une imprimante, un matériau et un profil donnés.
- [3D Print Toolbox](https://extensions.blender.org/add-ons/print3d-toolbox/) — extension Blender officielle pour analyser les maillages destinés à l’impression 3D.
- [Exemple avant/après](documentation/examples/README.md) — scène Blender et
  rendu synthétique reproductible.
- [Développement](documentation/DEVELOPMENT.md) — architecture, environnement,
  commandes de développement et validations.

## Développement

Avec Python 3.11, les tests du noyau mathématique peuvent être lancés ainsi :

```bash
python3.11 -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[test]'
python -m pytest -q
```

Les modules mathématiques n’importent pas `bpy`. Le guide de développement
décrit aussi le smoke test Blender et les validations qui restent à effectuer.

## Limites

Le contrôle topologique détecte certains défauts de connectivité et de
manifoldness. Il ne détecte pas les auto-intersections ni les surfaces
internes, et ne répare pas le maillage. Vérifie les dimensions et les alertes
du trancheur après export; le rapport de l’add-on ne garantit pas la
fabricabilité.
