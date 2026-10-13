# Internationalization (i18n)

## 1. Overview

CranioZ uses a centralized translation system with JSON catalogs organized by language and major functional area.

The system supports multiple languages, runtime language switching, contextual translation metadata, automatic fallback, and translation validation.

English is the source language. User-facing text can be translated into Portuguese, Spanish, and additional languages without changing application logic.

Internationalization affects presentation only. It must not change clinical calculations, persistent data, internal identifiers, or the meaning of clinical values.

The implementation must remain simple, predictable, and independent of clinical domain logic.

## 2. Architecture

The initial implementation consists of three components:

- **TranslationService:** Resolves translation keys, processes message parameters and pluralization, manages the active language, applies fallback rules, and notifies the interface when the language changes.
- **TranslationCatalogRegistry:** Locates, loads, and caches translation catalogs by language and functional area.
- **TranslationValidator:** Checks catalog structure, key coverage, source-text consistency, formatting parameters, and translation completeness.

Locale-specific formatting and physical-unit management are separate concerns. They may use dedicated services without becoming part of the translation mechanism.

Translation infrastructure belongs to the application infrastructure layer. Clinical domain logic must not depend on translated text or the active interface language.

## 3. Catalog Organization

Catalogs are organized by language and major functional area. Each area has one JSON catalog per language.

```text
translations/
├── en/
│   ├── core.json
│   ├── homepage.json
│   ├── workspace.json
│   ├── patient.json
│   ├── tomography.json
│   ├── cephalometry.json
│   └── osteotomy.json
└── pt-BR/
    ├── core.json
    ├── homepage.json
    ├── workspace.json
    ├── patient.json
    ├── tomography.json
    ├── cephalometry.json
    └── osteotomy.json
```

Language identifiers follow BCP 47 consistently across directory names, registry entries, and application preferences. For example, Brazilian Portuguese uses `pt-BR`.

Catalogs follow architectural responsibilities rather than individual screens or widgets.

- `core.json`: Shared terminology and application-wide messages.
- `homepage.json`: Homepage and project-selection interface.
- `workspace.json`: Workspace, editors, and shared interface elements.
- Module catalogs: Messages specific to clinical modules, such as tomography, cephalometry, and osteotomy.

Messages may be grouped into semantic categories within each catalog, but categories such as `interface`, `errors`, `help`, and `tooltips` are organizational conventions rather than mandatory structural requirements.

The registry resolves namespaced keys to the appropriate catalog. For example, `tomography.segmentation.failed` resolves to `tomography.json` and the `segmentation.failed` entry within that catalog.

## 4. Translation Keys and Catalog Format

Translation keys are stable semantic identifiers describing meaning or intent. They must not depend on the displayed text or a specific UI widget.

Example of `translations/en/tomography.json`:

```json
{
  "_metadata": {
    "module": "tomography",
    "language": "en",
    "format_version": 1
  },
  "segmentation": {
    "progress": {
      "message": "Processing scan... {percent}% complete.",
      "description": "Progress message displayed during segmentation."
    },
    "failed": {
      "message": "Segmentation could not be completed.",
      "description": "Displayed when segmentation fails."
    }
  }
}
```

Example of `translations/pt-BR/tomography.json`:

```json
{
  "_metadata": {
    "module": "tomography",
    "language": "pt-BR-BR",
    "format_version": 1
  },
  "segmentation": {
    "progress": {
      "message": "Processando tomografia... {percent}% concluído.",
      "description": "Mensagem exibida durante a segmentação."
    },
    "failed": {
      "message": "Não foi possível concluir a segmentação.",
      "description": "Exibida quando a segmentação falha."
    }
  }
}
```

Each translatable entry contains a `message` field and may include a `description` to clarify its intended meaning or usage.

Catalog metadata identifies the catalog and its format version. Translation maintenance data, such as source hashes and review status, may be generated or maintained by validation tools rather than being required at runtime.

The English catalog is the authoritative source for translation management.

## 5. TranslationService API

The TranslationService exposes a small, consistent API.

```python
tr(
    "tomography.segmentation.failed",
    "Segmentation could not be completed.",
)
```

The arguments are:

- `key`: Required semantic translation key.
- `source_text`: Required English source text, supplied as the second positional argument.
- Additional named arguments: Optional values used for message formatting.

The `source_text` argument is mandatory in application code. Omitting it is a static validation or lint error.

The source text provides a last-resort fallback if the translation cannot be resolved through the catalogs. It does not replace the English catalog as the authoritative source.

The TranslationValidator must detect discrepancies between the source text supplied in code and the corresponding English catalog entry.

The public API must not require a separate `default` argument.

## 6. Parameters and Pluralization

The TranslationService uses ICU MessageFormat through an established library. The project must not implement its own pluralization rules.

Named parameters allow dynamic values to be inserted into translated messages.

Example:

```python
tr(
    "tomography.segmentation.progress",
    "Processing scan... {percent}% complete.",
    percent=75,
)
```

Pluralization must be expressed explicitly using ICU MessageFormat.

Example:

```python
tr(
    "patient.count",
    "{count, plural, =0 {No patients selected} one {# patient selected} other {# patients selected}}",
    count=3,
)
```

The selected message follows the plural rules of the active language and the Unicode CLDR data used by the formatting implementation.

Passing a numeric parameter does not automatically pluralize a message. The catalog entry must contain the appropriate plural expression.

The validator must detect malformed expressions and inconsistent parameter names. Runtime formatting failures must be handled through the fallback mechanism.

## 7. Runtime Language Switching

The active interface language can be changed without restarting CranioZ.

When the language changes:

1. The TranslationService updates the active language.
2. Required catalogs are loaded or retrieved from cache.
3. A language-change notification is emitted.
4. Registered interface components refresh their translated text.

In the PySide6 interface, Qt signals and slots should propagate language-change notifications.

Interface components must explicitly participate in this mechanism. Calling `tr()` once during widget initialization does not automatically update the displayed text when the language changes.

The selected language is stored in application preferences. Language selection remains independent of regional formatting preferences.

## 8. Fallback and Error Recovery

The TranslationService follows a deterministic fallback sequence.

1. Look up the message in the active language catalog.
2. If unavailable, look up the message in the English source catalog.
3. If the English catalog or entry is unavailable, use the required English `source_text` supplied to `tr()`.
4. If no usable text can be produced, use a safe generic message appropriate to the context, when possible.

Example:

```python
tr(
    "tomography.segmentation.failed",
    "Segmentation could not be completed.",
)
```

The fourth step is an exceptional safeguard. It may be reached when the source text is invalid or empty, formatting fails, or another error prevents a usable message from being produced.

The system must never display an internal translation key, such as `tomography.segmentation.failed`, as ordinary user-facing text.

If no usable text can be resolved, the service must record a diagnostic error and display a safe generic message where appropriate. Critical clinical failures must remain explicit; a generic message must not conceal that an operation failed.

Missing-key diagnostics should be deduplicated or rate-limited to avoid repetitive logging.

Fallback is a runtime robustness mechanism, not a substitute for catalog validation.

## 9. Translation Maintenance and Validation

Translation maintenance is performed through automated validation tools rather than complex runtime infrastructure.

The TranslationValidator checks:

- Missing translation keys.
- Unused keys where static analysis can reliably identify them.
- Differences between source strings in code and the English catalog.
- Invalid catalog structures and metadata.
- Missing or inconsistent formatting parameters.
- Invalid ICU MessageFormat expressions.
- Incomplete translations in supported languages.
- Translations requiring review after a source-text change.

Source-text hashes may be used to detect changes. When used, the hash must be calculated from the authoritative English source message in the catalog, not from the translated text.

When an English source message changes, the maintenance process must identify affected translations and mark them for review. Existing translations must not be silently overwritten.

Review status and source hashes can be maintained by scripts or CI reports. They do not need to complicate the TranslationService runtime API.

Validation must run during development and in the continuous integration pipeline.

## 10. Key Extraction and Catalog Synchronization

A project-maintained script extracts translation keys and English source strings from supported `tr()` calls.

The extraction and synchronization process must:

1. Scan supported source files.
2. Collect translation keys and required source strings.
3. Compare extracted entries with the English catalogs.
4. Report missing entries and source-text discrepancies.
5. Identify unused entries where references can be established reliably.
6. Preserve existing translations when updating source catalogs.

Dynamic keys that cannot be discovered through static analysis must be declared explicitly in a registry or manifest.

The process must be repeatable and suitable for CI. The initial implementation does not require an external translation-management platform.

## 11. Catalog Loading and Caching

The TranslationCatalogRegistry loads catalogs on demand.

For example, core and homepage catalogs may be loaded during startup, while the osteotomy catalog is loaded when the corresponding module is opened.

The initial implementation uses a simple in-memory cache to avoid unnecessary file access.

The registry must:

- Load catalogs when required.
- Cache loaded catalogs.
- Load additional catalogs when the active language or application context requires them.
- Support explicit reloads for development and maintenance.
- Avoid blocking the interface during potentially expensive loading operations.

Advanced cache policies, distributed caching, and a full runtime catalog editor are outside the initial scope.

## 12. Rich Messages and User-Facing Content

The same TranslationService handles all user-facing text, including:

- Interface labels and buttons.
- Tooltips and contextual hints.
- Help content and tutorials.
- Notifications and error messages.
- Human-readable console messages.

Catalogs may contain ICU MessageFormat expressions and supported formatting constructs. Arbitrary HTML, executable content, and unrestricted markup are not permitted.

For bold text, links, and interactive elements, the interface controls rendering through structured content or explicitly supported markup. A translated string must not be treated as trusted HTML.

Long help documents may be maintained separately and referenced from the interface when appropriate.

## 13. Technical Logs and Identifiers

User-facing text may be translated. Technical identifiers must remain stable and independent of language.

Examples include:

- Command and event identifiers.
- Error codes.
- Machine-readable log fields.
- Serialized field names.
- Internal domain identifiers.

A segmentation failure may use the stable event code `SEGMENTATION_FAILED`, while its user-facing description is resolved through the TranslationService.

Debugging and support logs should preserve structured technical information and relevant original errors from external libraries. External library messages must not be assumed to be localizable through CranioZ catalogs.

## 14. Locale and Clinical Values

Language selection and regional formatting are separate concerns.

- **Interface language:** Determines the language of translated text.
- **Formatting locale:** Determines regional conventions for dates, decimal separators, and numeric presentation. It may follow the selected interface language or the operating system's regional settings, according to application preferences.
- **Physical units:** Managed independently through the UnitService.

For example, the same distance may be displayed as `12,50 mm` in a Portuguese regional format and `12.50 mm` in an English regional format.

Numerical values remain numeric internally. Clinical calculations, project files, DICOM data, geometry, and serialized values must not depend on localized display strings.

Unit conversion and locale-specific formatting are distinct operations. Localization must never silently change a measurement's physical meaning.

## 15. Adding Languages and Modules

Adding a language requires:

1. Creating the corresponding language catalogs.
2. Registering the language using a BCP 47 identifier, such as `en`, `pt-BR`, or `es`.
3. Running catalog validation.
4. Meeting the release-completeness requirements.

Existing catalogs must not require changes solely because a new language is introduced.

New modules register their catalogs through the TranslationCatalogRegistry and follow the same key, metadata, formatting, fallback, and validation conventions.

## 16. Release Validation

Development builds may allow incomplete translations, provided missing entries are reported.

Unless explicitly documented otherwise, a language is release-ready when all required entries in `core.json` and all catalogs for modules included in the release are translated and reviewed.

Application-level catalogs included in the release must meet the same requirements. Translations marked as requiring review do not count as reviewed until the required approval is completed.

The CI pipeline must validate catalog structure, required coverage, formatting consistency, and source-text synchronization before release.

Runtime fallback remains available as a robustness mechanism, but must not conceal translation defects during development, testing, or release validation.

## 17. Design Principles

- English is the authoritative source language.
- Translation keys are semantic and stable.
- Catalogs are organized by major functional area.
- TranslationService is shared across all user-facing content.
- The English source text argument to `tr()` is mandatory.
- Source text and English catalog entries are validated for consistency.
- ICU MessageFormat handles interpolation and pluralization.
- Language changes update the interface without restarting the application.
- Catalogs use lazy loading and a simple in-memory cache.
- Missing translations fall back to English and then to the source text supplied to `tr()`.
- Internal keys must never be displayed as ordinary user-facing messages.
- Translation validation and key extraction run automatically in CI.
- Locale formatting and physical-unit management remain separate from translation.
- Runtime fallback does not replace release validation.
- Translation affects presentation only and must not alter clinical calculations, persistent data, or machine-readable identifiers.

## 18. Initial Implementation Scope

The first implementation should prioritize:

1. JSON catalogs organized by language and functional area.
2. A small TranslationService API with mandatory source text.
3. A TranslationCatalogRegistry with lazy loading and simple caching.
4. ICU MessageFormat through an established library.
5. Runtime language switching using Qt signals and slots.
6. Explicit fallback behavior.
7. A TranslationValidator and source-catalog synchronization script.
8. CI checks for catalog consistency and release completeness.

An integrated translation editor, advanced catalog-reload workflows, external translation platforms, and elaborate metadata-management systems may be added later if project needs justify them.