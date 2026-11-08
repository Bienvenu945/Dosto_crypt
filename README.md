# DOSTO-CRYPT

> TEXT • BINARY • HEXADECIMAL

**Dosto-Crypt** est un outil interactif en ligne de commande (CLI) permettant de convertir du texte en données binaires ou hexadécimales, de générer des fichiers et de décoder des fichiers existants.

## Objectif du projet

Créer une application légère, modulaire et interactive permettant de :

- Saisir directement du texte dans une interface terminal.
- Convertir du texte en binaire brut ou en hexadécimal.
- Enregistrer les résultats dans des fichiers.
- Lire et décoder des fichiers binaires ou hexadécimaux.
- Visualiser les données sous forme hexadécimale.
- Analyser les propriétés et la structure des fichiers.

## Technologies

- Python 3
- Rich — interface terminal
- UTF-8 — encodage du texte
- Standard Library — manipulation des fichiers et des octets

## Architecture du projet

dosto-crypt/
│
├── main.py
├── requirements.txt
├── README.md
├── LICENSE
│
├── core/
│   ├── __init__.py
│   ├── converter.py
│   ├── file_manager.py
│   ├── detector.py
│   └── hexdump.py
│
├── interface/
│   ├── __init__.py
│   ├── menus.py
│   ├── prompts.py
│   └── display.py
│
├── utils/
│   ├── __init__.py
│   └── validators.py
│
└── tests/
    ├── test_converter.py
    ├── test_file_manager.py
    └── test_detector.py

## Feuille de route

### PHASE 1 — Moteur de conversion

- [ ] Conversion Texte → Binaire.
- [ ] Conversion Texte → Hexadécimal.
- [ ] Conversion Binaire → Texte.
- [ ] Conversion Hexadécimal → Texte.
- [ ] Gestion de l'encodage UTF-8.
- [ ] Gestion des caractères spéciaux et Unicode.
- [ ] Validation des données avant conversion.

### PHASE 2 — Gestion des fichiers

- [ ] Création de fichiers binaires `.bin`.
- [ ] Création de fichiers hexadécimaux `.hex`.
- [ ] Lecture des fichiers existants.
- [ ] Extraction du texte original.
- [ ] Vérification de l'intégrité des données.
- [ ] Gestion des erreurs de lecture et d'écriture.
- [ ] Affichage du nom, du type et de la taille des fichiers.

### PHASE 3 — Interface interactive

- [ ] Menu principal avec Rich.
- [ ] Saisie directe de texte.
- [ ] Mode de saisie multiligne.
- [ ] Sélection du format de sortie.
- [ ] Choix du nom et de l'emplacement du fichier.
- [ ] Messages de confirmation.
- [ ] Gestion des erreurs utilisateur.
- [ ] Navigation entre les différents menus.

### PHASE 4 — Analyse et visualisation

- [ ] Hex Viewer.
- [ ] Affichage des octets en hexadécimal.
- [ ] Représentation ASCII des données.
- [ ] Affichage des offsets.
- [ ] Aperçu des premiers octets.
- [ ] File Inspector.
- [ ] Détection du type de contenu.
- [ ] Analyse de la taille des fichiers.

### PHASE 5 — Confort et fonctionnalités avancées

- [ ] Historique des conversions.
- [ ] Conversion par lots.
- [ ] Prévisualisation avant exportation.
- [ ] Gestion des fichiers volumineux.
- [ ] Barre de progression.
- [ ] Exportation des résultats.
- [ ] Personnalisation de l'interface.
- [ ] Tests unitaires et tests de non-régression.

### PHASE 6 — Portabilité

- [ ] Compatibilité Kali Linux.
- [ ] Compatibilité Termux / Android.
- [ ] Compatibilité Windows.
- [ ] Génération d'un exécutable Linux.
- [ ] Génération d'un exécutable Windows avec PyInstaller.
- [ ] Documentation d'installation.

## Menu principal envisagé

DOSTO-CRYPT
TEXT • BINARY • HEXADECIMAL

1. Text to Binary / Hexadecimal
2. Binary / Hexadecimal to Text
3. Hex Viewer
4. File Inspector
5. Conversion History
6. Exit

## Formats pris en charge

| Format | Extension | Description |
|---|---|---|
| Binaire brut | `.bin` | Stockage des octets |
| Hexadécimal | `.hex` | Représentation textuelle des octets |
| Texte | `.txt` | Stockage du texte UTF-8 |

## Exemple de conversion

Texte original :

Bonjour

Représentation hexadécimale :

426f6e6a6f7572

Représentation binaire :

01000010 01101111 01101110 01101010
01101111 01110101 01110010

## Installation

```bash
git clone <URL_DU_DEPOT>
cd dosto-crypt

python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt

python main.py# DOSTO-CRYPT

> TEXT • BINARY • HEXADECIMAL

**Dosto-Crypt** est un outil interactif en ligne de commande (CLI) permettant de convertir du texte en données binaires ou hexadécimales, de générer des fichiers et de décoder des fichiers existants.

## Objectif du projet

Créer une application légère, modulaire et interactive permettant de :

- Saisir directement du texte dans une interface terminal.
- Convertir du texte en binaire brut ou en hexadécimal.
- Enregistrer les résultats dans des fichiers.
- Lire et décoder des fichiers binaires ou hexadécimaux.
- Visualiser les données sous forme hexadécimale.
- Analyser les propriétés et la structure des fichiers.

## Technologies

- Python 3.9+
- Rich — interface terminal
- UTF-8 — encodage du texte
- Standard Library — manipulation des fichiers et des octets

## Architecture du projet

```
dosto-crypt/
│
├── main.py
├── build.py                 # génération d'exécutable (PyInstaller)
├── requirements.txt
├── README.md
├── LICENSE
│
├── core/
│   ├── __init__.py
│   ├── converter.py         # texte <-> octets <-> binaire / hexadécimal
│   ├── file_manager.py      # lecture, écriture, intégrité, lots, inspection
│   ├── detector.py          # détection du type de contenu, entropie
│   ├── hexdump.py           # offsets / hexadécimal / ASCII
│   └── storage.py           # réglages et historique (JSON)
│
├── interface/
│   ├── __init__.py
│   ├── menus.py             # parcours et navigation
│   ├── prompts.py           # saisies
│   └── display.py           # rendu Rich
│
├── utils/
│   ├── __init__.py
│   └── validators.py
│
└── tests/
    ├── test_converter.py
    ├── test_file_manager.py
    ├── test_detector.py
    ├── test_hexdump.py
    ├── test_validators.py
    └── test_storage.py
```

## Feuille de route

### PHASE 1 — Moteur de conversion

- [x] Conversion Texte → Binaire.
- [x] Conversion Texte → Hexadécimal.
- [x] Conversion Binaire → Texte.
- [x] Conversion Hexadécimal → Texte.
- [x] Gestion de l'encodage UTF-8.
- [x] Gestion des caractères spéciaux et Unicode.
- [x] Validation des données avant conversion.

### PHASE 2 — Gestion des fichiers

- [x] Création de fichiers binaires `.bin`.
- [x] Création de fichiers hexadécimaux `.hex`.
- [x] Lecture des fichiers existants.
- [x] Extraction du texte original.
- [x] Vérification de l'intégrité des données.
- [x] Gestion des erreurs de lecture et d'écriture.
- [x] Affichage du nom, du type et de la taille des fichiers.

### PHASE 3 — Interface interactive

- [x] Menu principal avec Rich.
- [x] Saisie directe de texte.
- [x] Mode de saisie multiligne.
- [x] Sélection du format de sortie.
- [x] Choix du nom et de l'emplacement du fichier.
- [x] Messages de confirmation.
- [x] Gestion des erreurs utilisateur.
- [x] Navigation entre les différents menus.

### PHASE 4 — Analyse et visualisation

- [x] Hex Viewer.
- [x] Affichage des octets en hexadécimal.
- [x] Représentation ASCII des données.
- [x] Affichage des offsets.
- [x] Aperçu des premiers octets.
- [x] File Inspector.
- [x] Détection du type de contenu.
- [x] Analyse de la taille des fichiers.

### PHASE 5 — Confort et fonctionnalités avancées

- [x] Historique des conversions.
- [x] Conversion par lots.
- [x] Prévisualisation avant exportation.
- [x] Gestion des fichiers volumineux.
- [x] Barre de progression.
- [x] Exportation des résultats.
- [x] Personnalisation de l'interface.
- [x] Tests unitaires et tests de non-régression.

### PHASE 6 — Portabilité

- [x] Compatibilité Kali Linux.
- [ ] Compatibilité Termux / Android *(code portable : `pathlib` + bibliothèque standard + Rich ; à valider sur la cible)*.
- [ ] Compatibilité Windows *(idem)*.
- [ ] Génération d'un exécutable Linux *(`build.py` fourni ; à lancer sous Linux)*.
- [ ] Génération d'un exécutable Windows avec PyInstaller *(`build.py` fourni ; à lancer sous Windows)*.
- [x] Documentation d'installation.

## Menu principal

```
DOSTO-CRYPT
TEXT • BINARY • HEXADECIMAL

1. Text to Binary / Hexadecimal
2. Binary / Hexadecimal to Text
3. Hex Viewer
4. File Inspector
5. Conversion History
6. Exit
s. Settings
```

| Menu | Contenu |
|---|---|
| 1 | Saisie directe, saisie multiligne, conversion d'un fichier existant, conversion par lots d'un dossier |
| 2 | Décodage de binaire (0/1) saisi, d'hexadécimal saisi, ou lecture d'un fichier `.bin` / `.hex` / `.txt` |
| 3 | Visualisation paginée d'un fichier (offset, hexadécimal, ASCII), sans charger tout le fichier |
| 4 | Taille, dates, type détecté, entropie, SHA-256, aperçu des premiers octets |
| 5 | Dernières conversions, export JSON / CSV, effacement |
| s | Couleur d'accent, largeur du Hex Viewer, dossier de sortie par défaut |

**Conseils de saisie**

- Multiligne (texte) : terminez par une ligne `:fin` (ou Ctrl+D).
- Binaire / hexadécimal collé : terminez par une ligne vide. Espaces, retours à la ligne et préfixe `0x` sont tolérés.
- `Ctrl+C` annule l'opération en cours et revient au menu.

## Formats pris en charge

| Format | Extension | Description |
|---|---|---|
| Binaire brut | `.bin` | Stockage des octets |
| Hexadécimal | `.hex` | Représentation textuelle des octets (32 octets par ligne) |
| Binaire texte | `.txt` | Représentation 0/1 des octets (4 octets par ligne) |
| Texte | `.txt` | Stockage du texte UTF-8 |

À la relecture, `.bin` est lu comme octets bruts, `.hex` comme hexadécimal ; pour les autres extensions, le contenu est détecté (hexadécimal textuel, binaire textuel, sinon octets bruts). Un fichier texte qui ne contient *que* des chiffres hexadécimaux (ex. `cafe`) est donc interprété comme de l'hexadécimal.

Chaque écriture est **vérifiée** : le fichier est relu et comparé aux données d'origine (SHA-256 affiché). Les écritures passent par un fichier temporaire puis un renommage atomique, et aucun fichier existant n'est écrasé sans confirmation.

## Exemple de conversion

Texte original :

```
Bonjour
```

Représentation hexadécimale :

```
426f6e6a6f7572
```

Représentation binaire :

```
01000010 01101111 01101110 01101010
01101111 01110101 01110010
```

## Installation

```bash
git clone <URL_DU_DEPOT>
cd dosto-crypt

python -m venv .venv
source .venv/bin/activate        # Windows : .venv\Scripts\activate

pip install -r requirements.txt

python main.py
```

**Termux (Android)** : `pkg install python`, puis `pip install -r requirements.txt` et `python main.py`.

## Tests

```bash
python -m unittest discover -v   # bibliothèque standard
# ou : pytest
```

## Générer un exécutable

PyInstaller ne fait pas de compilation croisée : lancez la commande sur le système cible.

```bash
pip install pyinstaller
python build.py                  # produit dist/dosto-crypt (ou dist\dosto-crypt.exe)
```

## Données de l'application

Réglages et historique sont stockés dans `~/.dosto-crypt/` (`settings.json`, `history.json`). Le dossier peut être changé avec la variable d'environnement `DOSTO_CRYPT_HOME`.

## Licence

MIT — voir [LICENSE](LICENSE).
