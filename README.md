# Clone Relief for Blender

Clone Relief est un add-on Blender expérimental qui transfère le relief d’une
zone source vers une zone cible du même maillage. Il agit sur la géométrie et
permet de régler le transfert avant de l’appliquer.

**Version :** 0.1.0 · **Blender cible :** 4.5.8 LTS · **Plateforme de référence :** macOS Intel

> Clone Relief est un prototype. Il n’est pas encore qualifié pour garantir
> qu’un maillage soit imprimable.

## Sommaire

- [Compatibilité et état](#compatibilité-et-état)
- [Installation](#installation)
- [Utilisation rapide](#utilisation-rapide)
- [Documentation spécialisée](#documentation-spécialisée)
- [Développement](#développement)
- [Limites](#limites)

## Compatibilité et état

Clone Relief vise Blender **4.5.8 LTS**. La version 0.1.0 fournit la capture
d’une zone source et d’une cible, l’aperçu, l’application annulable et la
réapplication depuis la cible capturée. Le contrôle topologique et la
localisation de composantes déconnectées ont aussi été utilisés sur un scan.

La comparaison avant/après et le parcours d’export STL restent à valider de
bout en bout. M6 s’appuie sur le 3D Print Toolbox pour les contrôles de
fabricabilité dans Blender, puis vérifie l’export dans le trancheur et par une
impression représentative. Voir le [protocole de qualification](documentation/PRINT_QUALIFICATION.md).

## Installation

Depuis une copie locale du dépôt, construis l’archive de l’add-on :

```bash
python3.11 scripts/build_addon_zip.py
```

Le script crée `dist/blender_clone_relief_0.1.0.zip`. Dans Blender :

1. Ouvre **Blender → Preferences → Get Extensions**.
2. Dans le menu en haut à droite, choisis **Install from Disk…**, puis
   sélectionne l’archive ZIP.
3. Dans les préférences, recherche **Clone Relief** et active l’add-on.
4. Dans la vue 3D, ouvre la barre latérale avec **N**, puis choisis l’onglet
   **Clone Relief**.

Le [guide utilisateur](documentation/USER_GUIDE.md) contient les détails
d’installation pour macOS et le parcours complet dans Blender.

## Utilisation rapide

Travaille sur une copie du maillage. Les captures et le transfert se font en
**Edit Mode**, sur le même objet :

1. Sélectionne les faces d’une zone source saine, puis clique **Capture Source**.
2. Sélectionne les faces de la zone à corriger, puis clique **Capture Target**.
3. Clique **Preview Effect**. Ajuste les paramètres et prévisualise à nouveau
   si nécessaire; le compte rendu apparaît sous **Preview Effect** et
   **Apply Relief**.
4. Clique **Apply Relief**. Tu peux modifier les paramètres et réappliquer :
   chaque application repart de la géométrie enregistrée par **Capture Target**.
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
