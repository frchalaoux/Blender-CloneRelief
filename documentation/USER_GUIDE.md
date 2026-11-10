# Guide utilisateur — Clone Relief

[English translation](USER_GUIDE.en.md)

**Prototype :** version 0.2.0 pour Blender 4.5.8 LTS. L’utilisateur confirme
qu’un essai sur une copie du scan Pika, suivi d’une impression représentative,
est correct à ce jour. Les paramètres détaillés ne sont pas consignés; cet
essai ne garantit pas l’imprimabilité d’autres modèles ou configurations.

**Langue :** l’interface de Clone Relief suit la langue choisie dans Blender
en français ou en anglais. Pour afficher les textes français, active
**Interface** dans **Edit → Preferences → Interface → Translation**. Les
autres langues de Blender affichent les textes anglais. La version 0.2.0
localise le panneau, les boutons, les dialogues, les infobulles et les rapports.

## Installation sur macOS

### Installer la Release publiée (parcours recommandé)

1. Télécharger l’[archive ZIP de Clone Relief 0.2.0](https://github.com/frchalaoux/Blender-CloneRelief/releases/download/v0.2.0/blender_clone_relief_0.2.0.zip). Ne pas la décompresser.
2. Dans Blender 4.5.8, ouvrir **Blender → Preferences → Get Extensions**.
3. Dans le menu en haut à droite, choisir **Install from Disk…** et sélectionner le ZIP téléchargé.
4. Dans les préférences, chercher **Clone Relief** et activer l’add-on.
5. Dans la vue 3D, ouvrir la barre latérale avec **N**, puis choisir l’onglet **Clone Relief**.

Pour ce parcours, il ne faut ni installer ni lancer Python séparément, ni avoir une copie du dépôt source. Blender exécute l’add-on avec le Python intégré à Blender. Cet interpréteur est distinct de la commande autonome `python3.11` utilisée dans les instructions de construction ci-dessous.

### Construire le ZIP depuis le code source (développeurs uniquement)

Ignore cette section si le but est seulement d’installer la Release publiée. Elle s’adresse aux développeurs qui reconstruisent le ZIP depuis le code source. Ici, `python3.11` désigne une installation autonome de Python 3.11 sur l’ordinateur, accessible comme commande dans le Terminal. Elle est distincte du Python intégré à Blender, même si le numéro de version est le même. Le script n’installe pas Python. Si le Terminal indique que `python3.11` est introuvable, il faut installer Python 3.11 séparément avant de lancer cette commande.

```bash
python3.11 scripts/build_addon_zip.py
```

La commande crée `dist/blender_clone_relief_0.2.0.zip`, mais **n’installe pas** l’add-on. Pour utiliser le ZIP construit, reprendre les étapes Blender ci-dessus et sélectionner le fichier situé dans `dist/`.

À l’activation de l’add-on et à l’ouverture d’un fichier Blender, la vue est préparée en **Solid**, avec **X-Ray désactivé** et la sélection de faces active.

Blender 4.5 documente l’installation depuis un fichier ZIP, y compris pour les add-ons historiques, dans le [guide officiel des Add-ons](https://docs.blender.org/manual/en/4.5/editors/preferences/addons.html).

## Protocole conseillé : capturer, prévisualiser, appliquer

Toutes les captures et l’application du relief se font en **Edit Mode**, sur le
même objet maillé :

1. Sur une copie de travail et en **Edit Mode**, choisir l’ombrage **Solid** et
   désactiver **X-Ray** afin que la sélection ne traverse pas l’objet. Sélectionner
   les faces d’une zone saine assez texturée, puis cliquer **Capturer la source**.
   Le panneau donne le nombre de faces et de sommets capturés. Si tu
   désélectionnes la zone ensuite, **Resélectionner la source** la rétablit.

   ![Dans la scène de démonstration, seul le profil strié source est sélectionné en orange.](images/source-selection-demo.jpg)

   *Démonstration synthétique : la sélection orange est limitée au profil source; la cible à droite reste désélectionnée.*

2. Sélectionner les faces de la zone cible, puis cliquer **Capturer la cible**.
   Les faces doivent former un morceau continu, relié par des arêtes. Si la
   sélection touche aussi de petits morceaux disjoints, l’outil garde le groupe
   dominant seulement s’il contient au moins deux fois plus de faces que tous
   les autres réunis; il affiche alors le nombre de faces écartées. Sinon, il
   refuse la capture. La source et la cible doivent être sans face commune.
   **Resélectionner la cible** rétablit ensuite la cible capturée, y compris après Apply.

   ![Dans la scène de démonstration, seule la cible plane à droite est sélectionnée en orange.](images/target-selection-demo.jpg)

   *La source striée reste visible à gauche pour repérer les deux zones du même maillage.*

3. Cliquer **Prévisualiser l’effet**. L’aperçu ne modifie pas le maillage : il indique
   combien de sommets bougeraient et le déplacement maximal en millimètres.
   Vous pouvez modifier les réglages et refaire l’aperçu autant de fois que voulu;
   chaque calcul repart de la géométrie mémorisée lors de **Capturer la cible**.
4. Si le panneau signale une cible trop grossière, lancer
   **Diagnostiquer la résolution**, puis **Densifier la cible…** et vérifier le
   nombre de faces estimé avant de confirmer. Densifier signifie ajouter des
   sommets et des faces à la zone cible pour qu’elle puisse représenter des
   détails plus fins. La subdivision invalide les captures :
   recapturer source et cible, puis refaire l’aperçu.
5. Si l’aperçu annonce un déplacement inférieur à **0,05 mm**, essayer le
   **Gain du relief** suggéré ou capturer une source plus texturée. Refaire
   l’aperçu jusqu’à obtenir une amplitude adaptée au résultat recherché.
6. Cliquer **Appliquer le relief**. Le panneau indique si l’opération a réussi, le
   nombre de sommets déplacés et leur déplacement maximal. La cible capturée
   reste la référence : vous pouvez changer les réglages, refaire l’aperçu et
   cliquer de nouveau sur **Appliquer le relief**. Chaque application remplace le
   résultat précédent depuis les coordonnées capturées, sans empiler le relief.
   L’opération est annulable avec **Undo**.

Pour traiter une autre zone, sélectionnez-la puis cliquez sur **Capturer la cible** :
cette capture devient la nouvelle géométrie de départ. Une modification de
topologie invalide toujours les captures et impose de recapturer source et
cible. Après une application, les modifications manuelles des sommets de la
cible seront remplacées par le prochain résultat calculé depuis la capture.

Les commandes **Resélectionner la source** et **Resélectionner la cible** restaurent les faces
sauvegardées en mémoire sans refaire la capture ni modifier la géométrie. Elles
nécessitent Edit Mode sur le même objet et une topologie inchangée. Les captures
disparaissent à la fermeture du fichier ou au rechargement de l’add-on.

La barre latérale affiche les comptes de faces et sommets capturés ainsi que le
dernier résultat ou message d’erreur. Un changement de topologie invalide les
captures.

### Repère dans l’interface

Le schéma ci-dessous présente les sections et commandes de l’onglet **Clone Relief**
actuelles. C’est un repère de lecture, pas une capture d’écran : Blender ajuste
la mise en page selon la taille du panneau et son thème.

![Schéma français de l’onglet Clone Relief dans la barre latérale N](images/clone-relief-panel-guide.svg)

Une capture refusée avec plusieurs groupes indique le nombre de morceaux
séparés par des arêtes. Garder uniquement le morceau souhaité et recapturer;
une tentative refusée ne remplace pas une capture antérieure valide. Si un
groupe dominant est retenu automatiquement, vérifier le nombre de faces
écartées avant de poursuivre.

## Réglages

| Réglage | Défaut | Effet |
|---|---:|---|
| Opacité de sélection | 0,08 (8 %) | Réduit le remplissage orange des faces sélectionnées pour mieux voir la maille. Affecte la couleur de sélection des vues 3D pendant l’activation de l’add-on; la valeur de thème d’origine est restaurée à sa désactivation. |
| Intensité | 1,00 | Copie le profil complet; une valeur plus faible réduit son amplitude. |
| Gain du relief | 1,0× | Multiplie l’amplitude transférée; une valeur supérieure à 1 exagère le relief. Réglable jusqu’à 100×. |
| Échelle du motif | 1,00 | Échelle physique du motif; 2,00 double sa longueur d’onde. |
| Atténuation du bord | 0,25 | Largeur relative du fondu depuis le bord cible. |
| Mode de transfert | Unidirectionnel | Copie le profil source en le décalant vers l’extérieur juste assez pour ne pas passer sous la cible. Le mode bidirectionnel conserve son profil signé autour du plan moyen. |
| Déplacement maximal | 0 | Aucun plafond; une valeur positive limite le déplacement en unités de scène. |

**Prévisualiser l’effet** calcule le résultat sans changer les coordonnées du maillage.
**Appliquer le relief** est la seule de ces étapes qui déplace les sommets.

Pour copier le profil sans changer son amplitude, garder l’intensité à 1, le
gain à 1 et l’échelle à 1. Le fondu atténue volontairement le déplacement
près du bord; réduire sa largeur si l’on veut limiter cette zone de raccord.

Les messages distinguent réussite, faible amplitude, absence de sommet déplacé
et erreur de capture ou de topologie. Ils sont présentés ligne par ligne dans
le panneau juste sous les commandes **Prévisualiser l’effet** et
**Appliquer le relief**, dans une zone défilante; chaque ligne peut être
sélectionnée, et **Copier le message complet** copie le texte complet. Une
réussite donne le compte des
sommets modifiés et le déplacement maximal. Un résultat sous 0,05 mm est signalé comme très faible;
ce seuil est un repère visuel, pas une garantie d’impression.

## Diagnostic et densification locale

Après les captures source et cible, **Diagnostiquer la résolution** compare le 90e
percentile de longueur d’arête cible à la médiane de la source. Au-delà de
`1,5×`, le panneau signale une cible potentiellement trop grossière et propose
un nombre de coupes. Ce seuil est indicatif; il ne garantit pas que le motif
transféré sera correctement échantillonné.

**Densifier la cible…** ouvre une boîte de confirmation avec le nombre de coupes,
une estimation prudente du nombre de faces et le plafond ajouté (250 000 par
défaut). Vérifier l’estimation avant de confirmer. La subdivision conserve les
positions des bords et peut subdiviser les faces voisines qui partagent les
arêtes de la cible. Après l’opération, recapturer source et cible.

## M5 : contrôle, comparaison et export STL

Dans **M5. Contrôle du maillage**, **Contrôler la topologie pour l’impression**
analyse l’objet maillé actif. Le rapport indique les composantes reliées par
arêtes, les bords ouverts, arêtes filaires et non-manifold, sommets
non-manifold ou isolés et faces dégénérées. Il ne modifie pas le maillage.
Plusieurs composantes peuvent être voulues, et un résultat sans défaut détecté
ne certifie pas qu’un solide soit imprimable : les auto-intersections et
surfaces internes ne sont pas recherchées.

### Procédure pas à pas

1. Dans l’Outliner, déplie la scène et choisis le **maillage à examiner**.
   Réaffiche-le avec l’icône œil s’il est masqué, puis rends-le actif. Le
   contrôle porte sur cet objet uniquement; il ne combine pas plusieurs objets
   sélectionnés.
2. Clique **Contrôler la topologie pour l’impression**. Cette commande marche
   en Object Mode et en Edit Mode. Lis le compte rendu Clone Relief dans le
   panneau N, sous les commandes de l’add-on. Le rapport ne change pas la
   sélection ni la géométrie.
3. Lis **Composantes reliées par arêtes**. Une composante est un groupe de
   faces qui se rejoignent par des arêtes. Plusieurs composantes indiquent des
   îlots distincts dans ce même objet; cela ne signifie pas à lui seul qu’ils
   se croisent ou qu’il faut les supprimer.
4. Pour examiner un îlot, laisse le même objet actif, passe en **Edit Mode**,
   puis clique **Localiser une composante…**. Choisis dans la liste la ligne
   indiquant son rang et son nombre de faces, puis confirme. Clone Relief
   remplace la sélection courante par celle de cet îlot et cadre la vue dessus;
   il ne supprime ni ne déplace aucune géométrie.
5. Pour examiner un autre objet, quitte Edit Mode, choisis cet objet dans
   l’Outliner et recommence. « Localiser » ne s’active pas en Object Mode et
   n’a rien à proposer si l’objet actif ne comporte qu’une seule composante.
   Si la topologie change pendant que la liste de choix est ouverte, annule et
   relance la localisation.

Le nombre de composantes dépend de l’objet choisi. Dans le fichier d’analyse
M6 de la butternut, `BUTTERNUT_010` (original) en comporte trois;
`BUTTERNUT_010.001` (copie de travail) et `M6_FORMWARE_REPAIRED_TEMP` (STL
Formware importé) en comportent chacun une. Le contrôle topologique reste utile
sur le STL Formware, car il signale des bords ouverts, des arêtes non-manifold
et des faces dégénérées; le localisateur, lui, ne trouvera pas d’îlot distinct
dans cet objet.

Pour une analyse plus complète, Blender propose l’extension
[3D Print Toolbox](https://extensions.blender.org/add-ons/print3d-toolbox/),
compatible avec Blender 4.2 et ultérieur. Elle fournit notamment les contrôles
Solid, Intersections, Degenerate, Thickness, Shells, Edge Sharp et Overhang.
Le rapport Clone Relief reste utile pour repérer et localiser les composantes;
il ne remplace pas ces contrôles.

Après **Appliquer le relief**, cliquer **Comparer la cible avant/après** en Edit Mode
pour construire une paire temporaire de surfaces côte à côte depuis la cible
capturée et le résultat courant. Le maillage de travail est masqué pendant la
comparaison. Ces surfaces sont des copies ouvertes pour inspection visuelle,
pas des pièces imprimables. Cliquer **Revenir au maillage de travail** avant de
reprendre l’édition ou l’export. Cette comparaison porte uniquement sur les
faces de la cible capturée.

![Profil source, cible avant transfert et cible après transfert dans l’exemple synthétique.](examples/clone_relief_before_after.png)

*Résultat illustratif obtenu sur une scène de test; il ne prédit pas le résultat sur un scan réel.*

**Exporter le maillage actif en STL (mm)…** ouvre le sélecteur de fichier et
exporte uniquement l’objet maillé actif, avec ses modificateurs évalués. La
conversion en millimètres utilise l’échelle physique de la scène (`scale_length`)
et les transformations de l’objet. Un STL n’enregistre pas l’unité : contrôler
les dimensions importées dans le trancheur avant impression. Vérifier que
l’objet de travail est actif et que la comparaison temporaire a été effacée.
L’export est un contrôle de transfert; il ne répare ni ne certifie la
fabricabilité du maillage. Blender expose le choix d’export des objets
sélectionnés, l’échelle, l’unité de scène, les axes et l’application des
modificateurs dans son [manuel STL 4.5](https://docs.blender.org/manual/en/4.5/files/import_export/stl.html).

La qualification d’un résultat concret avec le 3D Print Toolbox, le trancheur
et une impression représentative est détaillée dans le
[protocole M6](PRINT_QUALIFICATION.md). Ce protocole ne constitue pas une
garantie générale d’imprimabilité.

## Validation sur une copie de la courge

Ne pas commencer sur l’original. Faire une copie du fichier ou du maillage de
travail, puis :

1. Confirmer les dimensions physiques et l’échelle objet dans Blender.
2. Choisir une zone source saine et une zone cible triangulée sur le même
   objet; éviter les bords ouverts, plis serrés et régions très courbes.
3. Capturer les régions et lancer **Diagnostiquer la résolution**. Consigner les
   valeurs source/cible et l’estimation.
4. Si la cible est sous-échantillonnée, choisir **Densifier la cible…**, vérifier
   le plafond et confirmer sur la copie.
5. Recapturer les deux régions, appliquer les réglages par défaut, puis
   examiner le relief sous lumière rasante.
6. Lancer le contrôle topologique, comparer la cible avant/après, puis effacer
   les surfaces de comparaison.
7. Exporter le seul objet de travail en STL, ouvrir le fichier dans Bambu Studio
   et vérifier les dimensions et avertissements.

Le transfert crée un motif plausible; il ne récupère pas les détails réellement
perdus du scan. Le prototype ne remplace pas une vérification des
auto-intersections, des parois internes, du manifoldness ou de la fabricabilité.

## Repères visuels

Les captures de sélection ci-dessus proviennent de la scène de démonstration
fournie avec le dépôt. Elles montrent les faces choisies, pas une capture réelle.
La [scène Blender synthétique](examples/README.md) permet de refaire le parcours
sans modifier un scan de production. Les panneaux de comparaison sont des surfaces
de démonstration ouvertes; ils ne sont pas des pièces imprimables.
