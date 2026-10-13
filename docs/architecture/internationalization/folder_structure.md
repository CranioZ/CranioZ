    cranioz/
    ├── pyproject.toml
    ├── README.md
    │
    ├── src/
    │   └── cranioz/
    │       ├── __init__.py
    │       ├── app.py                          # bootstrap Qt + wiring
    │       │
    │       ├── domain/
    │       │   ├── __init__.py
    │       │   └── ...
    │       │
    │       ├── infrastructure/
    │       │   ├── __init__.py
    │       │   └── i18n/
    │       │       ├── __init__.py             # get_translation_service()
    │       │       ├── instance.py             # configure() + singleton controlado
    │       │       ├── translation_service.py
    │       │       ├── catalog_registry.py
    │       │       └── catalog_loader.py
    │       │
    │       ├── settings/
    │       │   ├── __init__.py
    │       │   ├── preferences.py
    │       │   └── ...
    │       │
    │       ├── translations/                   # dados, não pacote
    │       │   ├── dynamic_keys.json
    │       │   ├── en/
    │       │   │   ├── core.json
    │       │   │   ├── homepage.json
    │       │   │   ├── workspace.json
    │       │   │   ├── patient.json
    │       │   │   ├── tomography.json
    │       │   │   ├── cephalometry.json
    │       │   │   └── osteotomy.json
    │       │   ├── pt-BR/
    │       │   │   └── ...
    │       │   └── es/
    │       │       └── ...
    │       │
    │       └── ui/
    │           ├── __init__.py
    │           ├── retranslatable.py
    │           └── ...
    │
    ├── tools/
    │   └── i18n/
    │       ├── pyproject.toml                  # cranioz-tools, depende de cranioz
    │       ├── src/
    │       │   └── cranioz_tools/
    │       │       └── i18n/
    │       │           ├── __init__.py
    │       │           ├── extract.py
    │       │           ├── sync.py
    │       │           └── validate.py
    │       └── tests/
    │           ├── test_extract.py
    │           ├── test_sync.py
    │           └── test_validate.py
    │
    └── tests/
        ├── conftest.py
        ├── infrastructure/
        │   └── i18n/
        │       ├── conftest.py
        │       ├── test_translation_service.py
        │       ├── test_catalog_registry.py
        │       └── test_catalog_loader.py
        └── ui/
            ├── conftest.py
            └── test_retranslatable.py