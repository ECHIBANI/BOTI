# 🤖 BOTI — Interpréteur de langage minimaliste en Python

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Version](https://img.shields.io/badge/Version-1.1-orange)]()

**BOTI** est un interpréteur de langage de programmation minimaliste écrit en Python pur, sans dépendances externes. Il implémente un pipeline complet : **Lexer → Parser → Interpréteur sémantique**, avec un mode REPL interactif et un support des fichiers `.boti`.

---

## ✨ Fonctionnalités

- ✅ **Opérations arithmétiques** : `+=`, `-=`, `*=`, `/=`
- ✅ **Affichage de texte** avec interpolation de variables : `"val = {x}"`
- ✅ **Commentaires** : `## mon commentaire ##`
- ✅ **Mode REPL interactif** avec état persistant des variables
- ✅ **Exécution de fichiers** `.boti`
- ✅ **Messages d'erreur structurés** : ligne | type | message | code source
- ✅ **Exécution partielle** : les lignes 1 → n-1 sont toujours exécutées avant une erreur
- ✅ **Initialisation implicite** : toutes les variables démarrent à `0`

---

## 🚀 Démarrage rapide

### Prérequis

- Python **3.10 ou supérieur** (pas de dépendances externes)

### Installation

```bash
git clone https://github.com/ton-utilisateur/boti.git
cd boti
```

### Lancer le REPL interactif

```bash
python main.py --repl
```

### Exécuter un fichier `.boti`

```bash
python main.py mon_programme.boti
```

### Voir l'exemple intégré

```bash
python main.py --exemple
```

### Mode par défaut (exemple + REPL)

```bash
python main.py
```

---

## 📖 Syntaxe du langage BOTI

### Opérations sur les variables

Toutes les variables sont initialisées à `0` implicitement.

```
x += 5        → ajoute 5 à x       (x = 0 + 5 = 5)
x -= 3        → soustrait 3 de x   (x = 5 - 3 = 2)
x *= 4        → multiplie x par 4  (x = 2 * 4 = 8)
x /= 2        → divise x par 2     (x = 8 / 2 = 4)
```

### Affichage de texte

```
"Bonjour le monde !"
"La valeur de x est : {x}"
"a = {a}  |  b = {b}"
```

### Commentaires

```
## Ceci est un commentaire ##
```

### Exemple complet

```boti
## Calcul du carré de 7 ##
n += 7
n *= 7
"Le carré de 7 est : {n}"

## Division ##
total += 100
total /= 4
"Total divisé par 4 : {total}"
```

**Sortie :**
```
Le carré de 7 est : 49
Total divisé par 4 : 25
```

---

## 🖥️ Commandes REPL

| Commande         | Description                          |
|-----------------|--------------------------------------|
| `vars`          | Affiche toutes les variables en mémoire |
| `aide`          | Affiche l'aide de la syntaxe BOTI    |
| `quitter` / `exit` / `q` | Quitte le REPL               |

---

## ⚙️ Options de la ligne de commande

| Commande                              | Description                          |
|---------------------------------------|--------------------------------------|
| `python main.py`                      | Exemple intégré puis REPL            |
| `python main.py --repl`               | REPL seul                            |
| `python main.py --exemple`            | Exemple seul                         |
| `python main.py fichier.boti`         | Exécute un fichier BOTI              |
| `python main.py fichier.boti --verbose` | Affiche les tokens et l'AST        |
| `python main.py fichier.boti --vars`  | Affiche les variables finales        |

---

## 🏗️ Architecture

```
boti/
├── main.py       # Point d'entrée : orchestration du pipeline, REPL, CLI
├── lexer.py      # Analyseur lexical : code source → liste de tokens
├── parser.py     # Analyseur syntaxique : tokens → AST
├── semantic.py   # Interpréteur sémantique : exécution de l'AST
├── examples/
│   └── demo.boti # Exemple de programme BOTI
├── tests/
│   └── test_boti.py  # Tests unitaires
├── README.md
├── LICENSE
└── .gitignore
```

### Pipeline d'exécution

```
Code source (.boti)
       │
       ▼
   [Lexer]  ──── analyse lexicale ────▶  Liste de Tokens
       │
       ▼
   [Parser] ──── analyse syntaxique ──▶  AST (Arbre Syntaxique Abstrait)
       │
       ▼
[Interpréteur] ── exécution ──────────▶  Résultat + Variables
```

---

## 🧪 Tests

```bash
python -m pytest tests/
```

Ou sans pytest :

```bash
python tests/test_boti.py
```

---

## 📄 Licence

Ce projet est sous licence **MIT** — voir le fichier [LICENSE](LICENSE) pour plus de détails.

---

## 👤 Auteur

Projet réalisé comme exercice d'implémentation d'un interpréteur de langage minimaliste en Python.
