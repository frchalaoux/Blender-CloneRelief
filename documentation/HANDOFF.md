# HANDOFF — Blender Clone Relief

[English translation](HANDOFF.en.md)

- **Date :** 10 novembre 2026
- **Dépôt :** Blender-CloneRelief, branche locale staging
- **Cible :** Blender 4.5.8 LTS sur macOS Intel; usage au trackpad, sans pavé numérique
- **État :** la release publique v0.2.0 est disponible. `staging`, le tag et
  la release pointent sur `0e918fd0f6589b45ab3a823bce99d82d280b3767`.
  L’archive `blender_clone_relief_0.2.0.zip` a pour SHA-256
  `93d546331d7e725e89573fbfb3df984bb317c5e29dbd4197ebd70868933f094c`.
  Les libellés ont été vérifiés par l’utilisateur en français et en anglais.
  Une impression représentative sur la copie Pika a été réalisée et déclarée
  correcte à ce jour; les paramètres détaillés ne sont pas consignés. Ce
  résultat ne constitue pas une garantie générale d’imprimabilité.
- **Release :** [Clone Relief v0.2.0 — interface FR/EN](https://github.com/frchalaoux/Blender-CloneRelief/releases/tag/v0.2.0)

## Objectif et décision fonctionnelle actuelle

Clone Relief copie le profil de surface d’une zone source sur une zone cible du
même maillage. En mode **unidirectionnel**, l’outil translate le profil complet
vers l’extérieur afin que son point le plus bas arrive sur la surface cible.
Les creux sont conservés et ne sont pas écrêtés. À intensité 100 %, gain 1× et
échelle 1×, le profil intérieur doit correspondre à la source à une translation
constante près. Le fondu de bord atténue volontairement le raccord.

Cette règle remplace l’ancienne approche qui extrayait seulement un résidu par
rapport à une surface lissée. Le résultat reste un motif transféré; il ne
reconstruit pas les détails absents du scan.

## État du produit

- **M0–M4 :** structure, noyau géométrique, captures source/cible, Apply/Undo,
  diagnostic et densification locale encadrée, panneau N, messages lisibles et
  copiables, guide macOS.
- **Sélection :** Solid, X-Ray désactivé et sélection de faces préparés à
  l’activation et à l’ouverture d’un fichier. Les captures refusent les modes
  susceptibles de sélectionner la face arrière. Les sélections disjointes
  sont signalées; un groupe dominant peut être retenu avec indication des faces
  écartées.
- **Transfert :** extraction du profil complet par rapport au plan moyen; le
  mode unidirectionnel translate tout le profil au-dessus de la cible. Le mode
  bidirectionnel garde les déplacements signés. Le gain est séparé de
  l’intensité. La nouvelle logique locale conserve les coordonnées initiales
  de la cible capturée; changer les réglages puis refaire Apply doit remplacer
  le résultat précédent plutôt que l’empiler.
- **Opacité :** un réglage local du panneau réduit l’alpha du remplissage
  orange de sélection; il doit restaurer le thème initial à la désactivation.
- **Densification :** commande locale confirmée, estimation de coût, plafond
  initial de 250 000 faces ajoutées et limite de 8 coupes. Elle invalide les
  captures. Pas encore éprouvée sur un gros scan réel.
- **Exemple :** documentation/examples/clone_relief_before_after.blend et son
  rendu PNG montrent le profil source échantillonné, la cible plane avant et
  la cible après. Paramètres : intensité 1, gain 1, échelle 1, fondu 0,1.
- **M5 :** audit topologique sans mutation, comparaison temporaire de la
  cible capturée avant/après Apply et export STL limité à l’objet actif, avec
  conversion `scale_length` vers les millimètres. L’audit n’inspecte pas les
  auto-intersections ni les surfaces internes. Le dossier d’add-on Blender
  installé correspond aux sources locales; le localisateur a été enregistré
  dans la session active et utilisé par l’utilisateur. Le compte rendu du dernier
  opérateur est affiché juste sous Preview/Apply pour rester visible près de
  son action. Les commandes **Resélectionner la source** et
  **Resélectionner la cible** restaurent les faces capturées en Edit Mode tant
  que l’objet et sa topologie correspondent.
  **Localiser une composante…** permet de choisir un groupe par nombre de faces,
  le sélectionne et cadre la vue sans modifier sa géométrie.
- **Localisation FR/EN :** `src/clone_relief/i18n.py` centralise les textes
  visibles; les boutons dessinés explicitement utilisent aussi ce catalogue.
  La version française de la preview a été validée par l’utilisateur.

## Validation et point de reprise

- L’utilisateur a confirmé que la preview FR affichait correctement le panneau
  après correction des libellés de boutons; la release v0.2.0 contient ce code.
- La compilation Python, la cohérence des versions dans le ZIP, le contenu de
  l’archive et `git diff --check` ont été vérifiés avant le commit. Aucune suite
  pytest ni aucun test d’intégration automatisé Blender n’a été lancé pour
  cette release.
- GitHub confirme que `staging`, `v0.2.0` et la release pointent sur le commit
  indiqué plus haut, et que le SHA-256 de l’asset correspond à celui publié.
- L’utilisateur confirme que les libellés de v0.2.0 sont corrects en anglais
  dans Blender.
- L’utilisateur confirme qu’une impression représentative du résultat sur la
  copie Pika a été réalisée et que tout est correct pour le moment. Machine,
  matériau, trancheur, profil et mesures ne sont pas consignés.
- L’utilisateur a choisi et autorisé la licence GPL-3.0-or-later pour
  publication sur Blender Extensions. Le manifeste a été ajouté et le paquet
  `dist/clone_relief-0.2.0.zip` construit avec Blender 4.5.8; la validation du
  manifeste source et de l’archive réussit. SHA-256 :
  `9cbad4b0a0611fc87246b02c8c592efc948317a81e0791765013ce99e82bb7dd`.
- L’utilisateur confirme que le test d’installation du paquet d’extension
  fonctionne. Le 10 novembre 2026, l’utilisateur indique que Blender examine
  maintenant la soumission; ce statut de revue est rapporté par l’utilisateur
  et n’a pas été vérifié indépendamment.
- Brouillon de description : « Clone Relief transfers the surface profile
  selected in one region of a mesh onto a selected target region of the same
  mesh. Capture source and target faces, preview the transfer, tune intensity,
  gain, scale, edge falloff and direction, then apply. Includes topology and
  component diagnostics, before/after comparison, bounded local densification,
  and selected-object STL export in millimeters. It does not guarantee
  printability. »
- Aperçu anglais sobre, en 16:9 et 1920 × 1080, prêt à joindre à la fiche :
  `documentation/examples/clone_relief_before_after.en.png`. Il montre le
  profil source, la cible plane avant transfert et le résultat après.
- Image principale (Featured Image) préparée en PNG, 1920 × 1080 :
  `documentation/images/clone-relief-featured-image-1920x1080.png`. Elle montre
  le profil source transféré sur une cible visiblement courbe, avec les reliefs
  qui suivent la courbure.
- Suite : attendre la décision de modération de Blender Extensions, puis
  consigner le résultat et traiter tout retour éventuel.

Le 9 novembre, un traceback pendant le dessin du panneau indiquait que l’icône
`MOD_DIFFERENCE` du bouton de comparaison n’existe pas dans Blender 4.5. Cette
erreur interrompait le rendu de la section M5. L’icône a été remplacée par
`MODIFIER`, valide dans Blender 4.5; recharger l’add-on installé pour appliquer
la correction.

Dans le fichier M6 rouvert, l’objet actif est `BUTTERNUT_010.001` en Edit Mode;
le rapport sur cet objet indique une composante. `BUTTERNUT_010` (original)
en a trois et `M6_FORMWARE_REPAIRED_TEMP` en a une. Le contrôle topologique
analyse seulement l’objet actif; le localisateur exige Edit Mode et au moins
deux composantes dans cet objet. Voir la procédure détaillée dans
[`USER_GUIDE.md`](USER_GUIDE.md#procédure-pas-à-pas).

## Dernier état du projet Blender observé — 7 novembre 2026

Aucun nouveau fichier Blender ni nouvel état de scène n’a été confirmé après
ces observations. Depuis, l’utilisateur a confirmé les libellés anglais de
v0.2.0 et une impression Pika correcte à ce jour; les paramètres de cet essai
restent à consigner.

Le dernier état observé dans Blender est le fichier Pika
`/Users/frchalaoux/Documents/print3D/Pika/tests/Scans/butternot/butternote.blend`.
`BUTTERNUT_010.001` est la copie de travail active; `BUTTERNUT_010` reste
masqué. Avec la version précédemment installée de l’add-on, une capture source
de 1 542 faces/830 sommets et une cible de 1 268 faces/694 sommets ont été
utilisées. Le dernier Apply a modifié 564 sommets, avec un déplacement maximal
de 0,537 mm (intensité 0,6, gain 1×, échelle 1, fondu 0,25, mode OUTWARD).
Le fichier était marqué modifié et n’était pas enregistré. Lors de la reprise
M5, le fichier était toujours ouvert en Edit Mode sur `BUTTERNUT_010.001`; le
dernier état M4 affichait une source de 1 572 faces/846 sommets, une cible de
2 758 faces/1 457 sommets, 1 106 sommets déplacés et un maximum de 1,065 mm.
L’opacité était 0,08. Un relevé topologique en lecture seule de la copie
indiquait 165 523 sommets, 484 984 arêtes et 319 251 faces, répartis en trois
composantes de 304 013, 10 562 et 4 676 faces; aucun bord ouvert, filaire,
non-manifold ou dégénéré n’avait été relevé. Ce relevé est un état observé,
pas encore le rapport émis par la nouvelle commande M5.

### État après localisation et suppression — 7 novembre 2026

L’utilisateur a localisé et supprimé les deux composantes internes jugées
inutiles. Lecture seule de Blender après cette opération :
`BUTTERNUT_010.001` est actif en Edit Mode et compte 157 964 sommets, 462 127
arêtes et 304 013 faces, soit le compte de faces de la grande composante
précédente. Le contrôle M5 a ensuite
été relancé et a trouvé une seule composante, zéro bord ouvert, arête filaire,
arête/sommet non-manifold, sommet isolé ou face dégénérée. Au moment de ce
contrôle, Blender indiquait `bpy.data.is_dirty = false`; l’utilisateur confirme
avoir sauvegardé le fichier. L’audit ne vérifie pas
les auto-intersections ni les surfaces internes. La géométrie n’a pas été
modifiée par l’assistant.

Les captures sont en mémoire et ne survivent pas à la réouverture du fichier.
Le code M5 est chargé dans la session courante; le localisateur a servi à
identifier les deux composantes supprimées par l’utilisateur. Les captures
source/cible sont à recapturer si elles ont été perdues lors du rechargement.

**Contexte d’installation observé le 7 novembre :** le pont Blender chargeait l’add-on depuis
`~/Library/Application Support/Blender/4.5/scripts/addons/clone_relief/`, alors
que le code de référence est dans `src/clone_relief/`. L’archive
`dist/blender_clone_relief_0.1.0.zip` a alors été reconstruite et le dossier
d’installation Blender synchronisé. L’utilisateur a sauvegardé le fichier Pika
après le nettoyage. La release courante est désormais v0.2.0.

M6 réutilise le 3D Print Toolbox pour les analyses géométriques de
fabricabilité, puis qualifie un cas d’impression identifié sans promesse
générale. Le protocole est dans
[`PRINT_QUALIFICATION.md`](PRINT_QUALIFICATION.md). Pour la copie Pika,
comparaison du transfert, contrôles avec le Toolbox, export et dimensions STL
dans le trancheur, aperçu des couches et impression réelle sont encore à faire.

Un nouveau contrôle en lecture seule a été lancé le 7 novembre 2026 sur
`BUTTERNUT_010.001` en Edit Mode. L’audit Clone Relief a compté 157 952
sommets, 462 083 arêtes et 303 981 faces, une composante, et zéro bord ouvert,
arête filaire/non-manifold, sommet isolé/non-manifold ou face dégénérée.
Le 3D Print Toolbox a rapporté 0 arête non-manifold, 0 mauvaise continuité,
1 coque, 349 faces signalées en intersection, 3 faces quasi nulles, 0 arête
nulle, 563 faces non planes, 5 651 faces minces au seuil de 1 mm, 310 arêtes
vives au seuil de 160° et 50 498 surplombs au seuil de 45°.

Les deux groupes de 45 et 21 faces ont été inspectés visuellement et présentent
une intersection nette; les autres résultats d’intersection et les 3 faces
quasi nulles restent à examiner. Les comptes d’épaisseur et de surplomb
dépendent des seuils et de l’orientation courante. Blender indiquait
`bpy.data.is_dirty = true` avant et après le
contrôle. Ne pas supposer que l’état courant est sauvegardé; aucune géométrie
n’a été éditée ni sauvegardée par l’assistant.

L’utilisateur précise que certains des groupes signalés en intersection ont
été créés par inadvertance avec des outils de sculpture. Les deux groupes
inspectés présentent une intersection, mais leur origine sculpturale n’est pas
établie. Ne pas supprimer en bloc les 349 faces : elles appartiennent au
maillage connecté et leur suppression pourrait ouvrir la surface.

Une comparaison spatiale lecture seule avec l’original caché, dont la matrice
monde est identique à celle de la copie, donne une distance médiane centre de
face → surface originale de 2,84 mm pour les 349 faces signalées (P90 8,32 mm).
Sur 2 000 faces non signalées prises à intervalles réguliers, la médiane est
0 mm (P90 4,00 mm). Comme il ne s’agit pas de correspondances sommet à sommet
et que les résolutions diffèrent, cela rend l’hypothèse de zones sculptées
plausible mais ne prouve pas la cause ni la nature de chaque intersection.

Sur les deux zones montrées par l’utilisateur, le contrôle BVH rapporte 53
paires de faces en chevauchement entre le groupe de 45 faces et celui de 21;
48 paires ne partagent aucun sommet, 5 en partagent un. Cette preuve numérique
explique que la traversée soit difficile à discerner dans le maillage dense.
Après isolement temporaire du voisinage, l’utilisateur confirme voir une
intersection nette. Cette validation visuelle concerne les deux groupes
inspectés seulement; ne pas supprimer les faces sélectionnées. La géométrie
n’a pas été modifiée. Le maillage complet est de nouveau visible et les 66
faces des groupes sont seules sélectionnées pour poursuivre l’inspection.
Un extrait temporaire de 11 809 faces de l’original est superposé à sa
position, semi-transparent et sans affichage forcé au premier plan. L’utilisateur
le voit derrière la copie depuis un angle, puis devant après une rotation de
25°. Un contrôle BVH lecture seule entre toute la copie (303 981 faces) et
l’extrait (11 809 faces), epsilon 1e-5 local, ne trouve aucun chevauchement de
triangles. L’ordre avant/arrière perçu dépend donc de la projection; les deux
groupes orange restent, eux, en chevauchement entre eux.

L’utilisateur a soumis `BUTTERNUT_010.001.stl` à Formware Online STL Repair.
L’analyse avant réparation rapporte 911 arêtes nues, 253 trous plans,
0 trou non-plan, 257 arêtes non-manifold, 446 normales inversées, 436 faces
dupliquées, 752 faces dégénérées et aucune coque disjointe. La réparation a
ajouté 6 170 sommets et 17 370 triangles. Le rapport ne donne pas d’analyse des
défauts résiduels après réparation; comparer le STL réparé à la copie Blender,
puis le réanalyser et le vérifier dans le trancheur.

Le STL réparé fourni (`Analyse Butternut M6 010.001.stl`) a été importé
temporairement dans Blender 4.5.8 à l’échelle 0,001. Ses dimensions
(103,851 × 238,163 × 111,197 mm) correspondent à celles du travail. Une
comparaison de 5 000 sommets échantillonnés dans chaque sens donne médiane 0,
P90 0,0038 mm, maximum 0,0087 mm vers l’autre surface. Toutefois l’import
Blender signale encore 363 arêtes à une face, 1 496 arêtes à plus de deux faces
et 3 382 faces d’aire nulle; une lecture directe du binaire trouve 2 648
triangles d’aire exactement nulle. L’import donne 330 614 triangles contre
332 822 facettes dans le STL. Ces comptes restent distincts; ne pas conclure
que la réparation a rendu le maillage manifold. Pas encore d’analyse par le
trancheur ni d’essai d’impression.

La comparaison des groupes 45/21 faces à l’original trouve une distance
médiane centre de face → surface de 8,32 mm pour chacun, contre environ
8,12 mm pour les faces non signalées proches. L’éloignement concerne donc
plus largement la région; ce relevé ne désigne pas les seules faces à corriger.

## Scan Pika

Fichier de travail déjà utilisé :
/Users/frchalaoux/Documents/print3D/Pika/tests/Scans/butternot/butternote.blend.
L’objet original est BUTTERNUT_010; l’objet de travail est
BUTTERNUT_010.001. Garder l’original intact et travailler sur une copie avant
toute application ou densification. Les mesures de relief et de résolution
faites avec l’ancienne extraction lissée doivent être refaites avec le profil
complet actuel.

## Validations acquises avant M5

- .venv/bin/python -m pytest -q : **22 tests réussis**.
- Smoke test exécuté avec Blender **4.5.8 LTS** : captures, mode de sélection,
  aperçu sans mutation, Apply/Undo, diagnostic et subdivision locale validés
  sur maillage synthétique.
- scripts/create_before_after_example.py exécuté avec Blender 4.5.8; le
  fichier blend et le PNG ont été régénérés.
- git diff --check sans erreur avant le commit de reprise.

Lors de la session du 7 novembre, les sources installées correspondaient aux
fichiers de référence; la cible capturée était conservée entre les Apply et
l’opacité observée était 0,08. L’audit M5 et le localisateur ont été utilisés
sur la copie Pika; après la suppression des composantes internes, l’audit a
confirmé une composante fermée sans défaut topologique détecté. L’export STL,
la vérification de dimensions et les auto-intersections/surfaces internes
restent à contrôler. Aucun test automatisé n’a été lancé pendant cette reprise.

Ces validations synthétiques ne remplacent pas l’inspection du résultat sur la
courge ni le contrôle de topologie/manifoldness pour impression.

## Prochaine action

1. Attendre le résultat de la revue Blender Extensions et traiter les retours.
2. Compléter ultérieurement le relevé M6 avec les détails d’impression
   disponibles.

L’impression réalisée est encourageante pour ce cas et cette configuration;
elle ne garantit pas l’imprimabilité d’autres maillages ou configurations.
