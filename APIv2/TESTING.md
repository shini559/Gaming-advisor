# Guide de Test - GameAdvisor API v2

## Types de Tests

### Tests Standard (par défaut)
```bash
pytest -v
# ou
pytest
```
Exécute tous les tests **sauf** les tests de connexion aux dépendances externes.

### Tests de Connexion aux Dépendances Externes
```bash
pytest -m connection -v
```
Tests de connectivité à Azure Blob Storage, Redis, etc. Nécessite la configuration des services externes.

### Tests de Dépendances Externes (tous)
```bash
pytest -m external_deps -v
```
Tous les tests qui nécessitent des services externes (inclut les tests de connexion).

### Tests par Catégorie
```bash
# Tests de sécurité seulement
pytest tests/integration/ -k "security" -v

# Tests d'intégration
pytest -m integration -v

# Tests unitaires
pytest -m unit -v
```

### Combinaisons
```bash
# Tests standard + tests de connexion
pytest -v -m "not (connection and external_deps)"

# Tous les tests (y compris connexions)
pytest -v --override-ini="addopts="
```

## Marqueurs Disponibles

- `connection`: Tests de connectivité aux services externes
- `external_deps`: Tests nécessitant des dépendances externes
- `integration`: Tests d'intégration
- `unit`: Tests unitaires

## Configuration

La configuration pytest se trouve dans `pytest.ini`. Par défaut, les tests de connexion sont exclus des exécutions standard.