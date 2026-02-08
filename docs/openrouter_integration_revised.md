# OpenRouter OCR Integration - Revised Strategy

> [!NOTE]
> **Status: Implemented (v2.0)** - This document outlines the strategy that was implemented in Jan/Feb 2026. See `ARCHITECTURE.md` and `README.md` for the current state.

## 🎯 New Approach: Cloud-First with Free Tier

Since **Nemotron Nano 12B VL is completely FREE**, we should prioritize OpenRouter over RapidOCR for better quality and Myanmar support.

---

## 🔄 Revised Architecture

### Smart OCR Routing (Priority Order)

```python
if has_openrouter_key:
    # Priority 1: Free OpenRouter models
    if model == "free" or not specified:
        use Nemotron Nano 12B VL (FREE)
    elif model == "cheap":
        use Gemini 2.0 Flash Lite ($0.075/1M)
    elif model == "balanced":
        use Qwen 2.5-VL 32B ($0.05/1M)
    elif model == "quality":
        use Qwen 2.5-VL 72B ($0.15/1M)
    elif model == "premium":
        use Mistral Pixtral Large ($2/1M)
else:
    # Fallback: Local RapidOCR (no API key needed)
    if lang in ["en", "ch_sim", "ch_tra", "ja", "ko", "ru"]:
        use RapidOCR
    else:
        show error: "OpenRouter API key required for this language"
```

---

## 💡 Key Benefits

### Why OpenRouter First?

1. **FREE tier available** - Nemotron Nano 12B VL costs nothing
2. **Myanmar support** - All models support Myanmar + 100+ languages
3. **Better quality** - Vision models outperform traditional OCR
4. **Flexibility** - 5+ model options for different needs
5. **No installation** - Just API key, no dependencies

### RapidOCR as Fallback

- ✅ Works offline (no internet needed)
- ✅ No API key required
- ✅ Fast for supported languages (6 languages)
- ✅ Lightweight and efficient
- ⚠️ Limited language support (no Myanmar)

---

## 🎨 Updated UI Design

### Settings Panel

```
⚙️ Advanced Settings
├── OCR Engine: [Dropdown]
│   ├── OpenRouter (Cloud - Recommended) ⭐
│   └── RapidOCR (Local - 6 languages only)
│
├── ─── If OpenRouter selected ───
│   ├── Model: [Dropdown]
│   │   ├── Nemotron Nano 12B VL (FREE) ⭐ Default
│   │   ├── Gemini 2.0 Flash Lite (Ultra-fast, $0.08/1K pages)
│   │   ├── Qwen 2.5-VL 32B (Balanced, $0.05/1K pages)
│   │   ├── Qwen 2.5-VL 72B (Best quality, $0.15/1K pages)
│   │   └── Mistral Pixtral Large (Premium, $2/1K pages)
│   │
│   ├── API Key: [Password field]
│   │   └── Get free key at: openrouter.ai
│   │
│   └── 💰 Estimated Cost: FREE (or $X.XX per page)
│
├── ─── If RapidOCR selected ───
│   ├── DPI: [Slider: 150-600]
│   └── OCR Language: [Dropdown: en, ch_sim, ch_tra, ja, ko, ru]
│
├── Export Format: [Dropdown: MD, HTML, TXT, DOCX]
└── Page Range: [Start/End]
```

---

## 📊 Model Selection Guide

### Default Recommendation

**Nemotron Nano 12B VL (FREE)**

- Cost: $0.00
- Quality: ⭐⭐⭐⭐
- Speed: ⚡⚡⚡
- Languages: 100+
- Special: Video OCR support

### When to Use Each Model

| Model                     | Use When                  | Cost/1K Pages |
| ------------------------- | ------------------------- | ------------- |
| **Nemotron Nano 12B VL**  | Default choice, free tier | **FREE**      |
| **Gemini 2.0 Flash Lite** | Need fastest speed        | ~$0.08        |
| **Qwen 2.5-VL 32B**       | Best value for quality    | ~$0.05        |
| **Qwen 2.5-VL 72B**       | Maximum accuracy needed   | ~$0.15        |
| **Pixtral Large**         | Complex documents, SOTA   | ~$2.00        |
| **RapidOCR**              | No internet, offline use  | FREE (local)  |

---

## 🚀 Implementation Changes

### Phase 1: Core Integration (Updated)

1. ✅ Add OpenRouter client to `structure_engine.py`
2. ✅ Implement `extract_with_openrouter` function
3. ✅ Support 5 model options:
   - `nvidia/nemotron-nano-12b-v2-vl:free` (default)
   - `google/gemini-2.0-flash-lite-001`
   - `qwen/qwen2.5-vl-32b-instruct`
   - `qwen/qwen2.5-vl-72b-instruct`
   - `mistralai/pixtral-large-2411`
4. ✅ Add base64 image encoding
5. ✅ Test with Myanmar PDF

### Phase 2: UI Integration (Updated)

6. ✅ Add OCR engine dropdown (OpenRouter as default)
7. ✅ Add model selector with 5 options
8. ✅ Add API key input with validation
9. ✅ Show "FREE" badge for Nemotron model
10. ✅ Implement conditional settings visibility
11. ✅ Update conversion logic with cloud-first routing

### Phase 3: Enhancement

12. ✅ Real-time cost estimation
13. ✅ Usage tracking per model
14. ✅ Error handling with fallback to RapidOCR
15. ✅ API key persistence (optional)

---

## 💰 Cost Transparency

### Display Format

```
📊 Conversion Results
├── Method: OpenRouter (Nemotron Nano 12B VL)
├── Status: ✅ Success
├── Words: 1,234
├── Pages: 5
├── Time: 3.2s
└── Cost: FREE ⭐
```

### Monthly Tracking

```
📈 This Month's Usage
├── Total Pages: 150
├── OpenRouter (Free): 120 pages - $0.00
├── OpenRouter (Paid): 20 pages - $0.03
├── RapidOCR (Local): 10 pages - $0.00
└── Total Cost: $0.03
```

---

## 🔒 API Key Management

### Storage Options

1. **Session-only** (default) - Enter each time
2. **Environment variable** - Save to `.env`
3. **Encrypted config** - Save encrypted locally

### Security

- Never log API keys
- Mask in UI (show only last 4 chars)
- Validate before first use
- Clear on logout (if session-only)

---

## 📝 Updated Feature List

### OpenRouter Integration

- [x] 5 selectable models (Nemotron, Gemini, Qwen x2, Pixtral)
- [x] FREE default model (Nemotron Nano 12B VL)
- [x] Myanmar language support (all models)
- [x] Cost estimation and tracking
- [x] API key management
- [x] Fallback to RapidOCR (offline mode)

### RapidOCR Fallback

- [x] 6 language support (en, ch_sim, ch_tra, ja, ko, ru)
- [x] Offline operation
- [x] No API key required
- [x] Fast local processing

---

## 🎯 Success Metrics

### Goals

- ✅ Myanmar OCR support
- ✅ Zero cost for default usage (FREE model)
- ✅ < 5s per page processing time
- ✅ Offline fallback available
- ✅ 5+ model options for flexibility

### Expected Results

- **Cost**: $0.00 - $0.50 per 1,000 pages (vs $1.50 Google Cloud Vision)
- **Quality**: ⭐⭐⭐⭐ (vision models > traditional OCR)
- **Speed**: 3-5s per page
- **Languages**: 100+ (vs 6 for RapidOCR)

---

## 🚀 Next Steps

1. ✅ Save analysis to codebase (`docs/openrouter_models_analysis.md`)
2. ⏭️ Implement OpenRouter client in `structure_engine.py`
3. ⏭️ Update UI with model selector
4. ⏭️ Test with Myanmar PDF
5. ⏭️ Deploy and gather user feedback
