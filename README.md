# Blender Clone Relief

Prototype d’add-on Python pour transférer le microrelief géométrique d’une zone
saine d’un scan vers une zone cible du même maillage.

**État :** M0–M4 sont réalisés : noyau mathématique, captures, Apply/Undo,
diagnostic de résolution, densification locale encadrée et panneau N. La
validation sur une copie du scan Pika reste à faire. Le projet
cible Blender **4.5.8 LTS** sur macOS Intel.

## Documentation

- [Index de la documentation](documentation/README.md)
- [Spécifications fonctionnelles et critères d’acceptation](documentation/SPECIFICATIONS.md)
- [Handoff du projet et milestones](documentation/HANDOFF.md)
- [Développement, environnement et algorithme M1](documentation/DEVELOPMENT.md)
- [Guide utilisateur et installation macOS](documentation/USER_GUIDE.md)

## Développement rapide

Avec Python 3.11 :

```bash
python3.11 -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[test]'
python -m pytest -q
```

Les modules mathématiques n’importent pas `bpy`. Le guide de développement
documente l’environnement macOS/Blender 4.5.8 et les limites actuelles.
