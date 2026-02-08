# Changelog

All notable changes to this project will be documented in this file.

## [v2.0.0] - 2026-02-09

### 🚀 High-Fidelity Pipeline (Phase 1-4)

- **Tag-Don't-Remove Strategy**: Shifted from destructive cleaning to semantic tagging. Noise elements (headers, footers, watermarks) are now preserved and tagged (e.g., `<!-- role:header -->`) for downstream filtering, ensuring 100% content fidelity.
- **Normalization Engine**: Added `cleaner.normalize_markdown` to deterministically standardize spacing, list bullets, and line breaks before validation.
- **Data-Driven Validation**: Validation now uses PDF text layer word counts (when available) for accurate "Completeness" scoring, replacing generic page-based heuristics.
- **OpenRouter Integration**: Full support for OpenRouter Vision models (Qwen 2.5-VL, Nemotron) with "Balanced", "Quality", and "Fast" presets.
- **Myanmar Support**: Verified OCR support for Myanmar language via OpenRouter models.

### ✨ Improvements

- **Prompt Engineering**: Updated System Prompt to enforce strict Markdown styling (lists, tables, spacing).
- **Metadata Extraction**: Enhanced `metadata_extractor.py` to count words in PDF text layers.
- **Validation Rules**: Whitelisted `header`, `footer`, `page_number` roles to prevent false positives in quality reports.
- **Input Resolution**: Increased PDF rendering DPI to 300 for higher OCR accuracy.

### 🔧 Fixes

- Fixed hyphenation merging to be less aggressive.
- Fixed page number misclassification by using spatial heuristics.
- Fixed validation errors for "invalid roles" on legitimate noise elements.
