src/cranioz/
├── config/                          # ← inside the package
│   ├── __init__.py
│   ├── defaults/                    # ← default values
│   │   ├── app.json                 # (app default values)
│   │   ├── paths.json               # (paths default values)
│   │   └── logging.yaml             # (default logging config)
│   ├── loader.py                    # ← ConfigurationLoader
│   ├── schema.py                    # ← validation schemas
│   └── migration.py                 # ← schema migration
│
└── settings/                        # ← code, not data
├── __init__.py
    ├── user_settings.py             # ← UserSettings class
    ├── professional_settings.py     # ← ProfessionalSettings class
    ├── theme_settings.py            # ← ThemeSettings class
    ├── window_state.py              # ← WindowState class
    └── settings_manager.py          # ← orchestrator