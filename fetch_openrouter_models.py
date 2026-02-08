"""
Fetch all vision-capable OCR models from OpenRouter API
"""
import requests
import json

def fetch_openrouter_models():
    """Fetch all available models from OpenRouter"""
    url = "https://openrouter.ai/api/v1/models"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        # Filter for vision-capable models
        vision_models = []
        
        for model in data.get('data', []):
            model_id = model.get('id', '')
            name = model.get('name', '')
            description = model.get('description', '')
            architecture = model.get('architecture', {})
            
            # Check if model supports vision/multimodal
            modality = architecture.get('modality', '')
            context_length = model.get('context_length', 0)
            pricing = model.get('pricing', {})
            
            # Filter for vision models (multimodal or vision-specific)
            if 'multimodal' in modality.lower() or 'vision' in modality.lower() or \
               'vision' in name.lower() or 'pixtral' in model_id.lower() or \
               'qwen' in model_id.lower() and 'vl' in model_id.lower() or \
               'gemini' in model_id.lower() or 'nemotron' in model_id.lower() or \
               'llava' in model_id.lower() or 'glm' in model_id.lower():
                
                vision_models.append({
                    'id': model_id,
                    'name': name,
                    'description': description[:100] + '...' if len(description) > 100 else description,
                    'context_length': context_length,
                    'input_cost': pricing.get('prompt', 'N/A'),
                    'output_cost': pricing.get('completion', 'N/A'),
                    'modality': modality
                })
        
        return vision_models
    
    except Exception as e:
        print(f"Error fetching models: {e}")
        return []

def main():
    print("🔍 Fetching OpenRouter Vision Models...\n")
    
    models = fetch_openrouter_models()
    
    if not models:
        print("❌ No models found or error occurred")
        return
    
    print(f"✅ Found {len(models)} vision-capable models\n")
    print("=" * 100)
    
    # Sort by input cost (cheapest first)
    models_sorted = sorted(models, key=lambda x: float(x['input_cost']) if x['input_cost'] != 'N/A' else float('inf'))
    
    for i, model in enumerate(models_sorted, 1):
        print(f"\n{i}. {model['name']}")
        print(f"   ID: {model['id']}")
        print(f"   Description: {model['description']}")
        print(f"   Context: {model['context_length']:,} tokens")
        print(f"   Cost: ${model['input_cost']}/1M input, ${model['output_cost']}/1M output")
        print(f"   Modality: {model['modality']}")
    
    print("\n" + "=" * 100)
    
    # Save to JSON for reference
    with open('openrouter_vision_models.json', 'w') as f:
        json.dump(models_sorted, f, indent=2)
    
    print(f"\n💾 Saved {len(models_sorted)} models to openrouter_vision_models.json")
    
    # Print top recommendations for OCR
    print("\n🏆 TOP RECOMMENDATIONS FOR OCR:")
    print("-" * 100)
    
    ocr_keywords = ['qwen', 'pixtral', 'gemini', 'nemotron', 'ocr', 'document']
    ocr_models = [m for m in models_sorted if any(kw in m['id'].lower() or kw in m['name'].lower() for kw in ocr_keywords)]
    
    for i, model in enumerate(ocr_models[:10], 1):
        print(f"{i}. {model['name']} - ${model['input_cost']}/1M tokens")
        print(f"   {model['id']}")

if __name__ == "__main__":
    main()
