import asyncio
import aiohttp
import requests
from random import randint
from PIL import Image
import io
import os
from time import sleep
from dotenv import get_key
from pathlib import Path
import json
from bs4 import BeautifulSoup

# ===============================
# CONFIG
# ===============================
HUGGINGFACE_API_KEY = get_key('.env', 'HUGGINGFACE_API_KEY_2')

# Best quality models for accurate generation
MODELS = [
    {
        "name": "stabilityai/stable-diffusion-xl-base-1.0",
        "steps": 40,
        "guidance": 8.0
    },
    {
        "name": "stabilityai/stable-diffusion-2-1",
        "steps": 35,
        "guidance": 7.5
    },
    {
        "name": "runwayml/stable-diffusion-v1-5",
        "steps": 30,
        "guidance": 7.0
    }
]

HEADERS = {
    "Authorization": f"Bearer {HUGGINGFACE_API_KEY}",
    "Content-Type": "application/json"
}

# Create directories
Path("Data/Images").mkdir(parents=True, exist_ok=True)

# ===============================
# WEB SEARCH FOR VISUAL REFERENCES
# ===============================
async def search_visual_references(prompt: str) -> dict:
    """
    Search the web for visual descriptions and references
    Uses multiple free APIs to gather information
    """
    print(f"\n🔍 Searching web for references: '{prompt}'")
    
    references = {
        "description": "",
        "appearance": [],
        "details": []
    }
    
    try:
        # Method 1: Wikipedia search (Free, no API key needed)
        wiki_info = await search_wikipedia(prompt)
        if wiki_info:
            references["description"] = wiki_info
            print(f"✓ Found Wikipedia info")
        
        # Method 2: DuckDuckGo Instant Answer (Free, no API key)
        ddg_info = await search_duckduckgo(prompt)
        if ddg_info:
            references["appearance"].extend(ddg_info)
            print(f"✓ Found DuckDuckGo details")
        
        # Method 3: Google Custom Search (if you have API key - optional)
        # Uncomment if you add GOOGLE_SEARCH_API_KEY to .env
        # google_info = await search_google(prompt)
        # if google_info:
        #     references["details"].extend(google_info)
        
    except Exception as e:
        print(f"⚠️ Search error: {e}")
    
    return references

async def search_wikipedia(query: str) -> str:
    """
    Search Wikipedia for character/object descriptions
    """
    try:
        async with aiohttp.ClientSession() as session:
            # Wikipedia API - completely free
            url = "https://en.wikipedia.org/w/api.php"
            params = {
                "action": "query",
                "format": "json",
                "titles": query,
                "prop": "extracts",
                "exintro": True,
                "explaintext": True
            }
            
            async with session.get(url, params=params, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    pages = data.get("query", {}).get("pages", {})
                    
                    for page_id, page_data in pages.items():
                        if page_id != "-1":  # Page exists
                            extract = page_data.get("extract", "")
                            # Get first 500 chars for context
                            return extract[:500] if extract else ""
    except:
        pass
    
    return ""

async def search_duckduckgo(query: str) -> list:
    """
    Search DuckDuckGo for instant answers (100% free)
    """
    try:
        async with aiohttp.ClientSession() as session:
            url = f"https://api.duckduckgo.com/"
            params = {
                "q": query,
                "format": "json",
                "no_html": 1
            }
            
            async with session.get(url, params=params, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    details = []
                    
                    # Get abstract
                    if data.get("Abstract"):
                        details.append(data["Abstract"][:300])
                    
                    # Get related topics
                    for topic in data.get("RelatedTopics", [])[:3]:
                        if isinstance(topic, dict) and topic.get("Text"):
                            details.append(topic["Text"][:200])
                    
                    return details
    except:
        pass
    
    return []

# ===============================
# EXTRACT KEY VISUAL FEATURES
# ===============================
def extract_visual_features(references: dict, prompt: str) -> str:
    """
    Extract key visual features from search results
    """
    features = []
    
    # Combine all reference text
    all_text = references["description"] + " ".join(references["appearance"]) + " ".join(references["details"])
    all_text = all_text.lower()
    
    # Extract appearance keywords
    appearance_keywords = {
        "hair": ["white hair", "black hair", "blonde hair", "silver hair", "blue hair", "spiky hair", "long hair", "short hair"],
        "eyes": ["blue eyes", "green eyes", "red eyes", "golden eyes", "glowing eyes", "bright eyes"],
        "clothing": ["uniform", "suit", "armor", "dress", "jacket", "coat", "robe", "costume"],
        "colors": ["white", "black", "blue", "red", "green", "gold", "silver", "purple"],
        "accessories": ["glasses", "mask", "blindfold", "sword", "weapon", "crown", "hat"],
        "style": ["anime", "realistic", "manga", "cartoon", "superhero", "fantasy"]
    }
    
    for category, keywords in appearance_keywords.items():
        for keyword in keywords:
            if keyword in all_text:
                features.append(keyword)
    
    # Character-specific patterns
    character_patterns = {
        "gojo": ["white hair", "blue eyes", "blindfold", "black blindfold", "jujutsu kaisen", "anime character"],
        "naruto": ["blonde hair", "blue eyes", "orange jumpsuit", "headband", "ninja"],
        "luffy": ["straw hat", "red vest", "scar under eye", "anime", "pirate"],
        "superman": ["blue suit", "red cape", "s symbol", "muscular", "superhero"],
        "batman": ["black suit", "bat symbol", "cape", "cowl", "dark knight"],
    }
    
    # Check if prompt matches known characters
    for character, char_features in character_patterns.items():
        if character in prompt.lower():
            features.extend(char_features)
            break
    
    return ", ".join(features) if features else ""

# ===============================
# INTELLIGENT KEYWORD ANALYSIS
# ===============================
def analyze_prompt_intelligently(prompt: str) -> list:
    """
    Automatically detect what's in the prompt and add relevant keywords
    """
    prompt_lower = prompt.lower()
    enhancements = []
    
    # Detect anime/manga characters
    anime_keywords = ['anime', 'manga', 'character', 'gojo', 'naruto', 'luffy', 'ichigo', 'eren']
    if any(word in prompt_lower for word in anime_keywords):
        enhancements.extend([
            "anime art style",
            "detailed anime character",
            "vibrant colors",
            "sharp linework",
            "professional anime illustration"
        ])
    
    # Detect humans/people/characters
    human_keywords = ['person', 'man', 'woman', 'boy', 'girl', 'child', 'human', 'people', 
                      'character', 'portrait', 'face', 'selfie', 'model']
    if any(word in prompt_lower for word in human_keywords):
        enhancements.extend([
            "perfect human anatomy",
            "natural facial features",
            "symmetrical face",
            "realistic skin texture",
            "proper body proportions"
        ])
    
    # Detect specific body parts that often get distorted
    if any(word in prompt_lower for word in ['hand', 'hands', 'finger', 'fingers']):
        enhancements.extend([
            "anatomically correct hands",
            "exactly five fingers per hand",
            "proper finger proportions"
        ])
    
    # Detect animals
    animal_keywords = ['cat', 'dog', 'horse', 'bird', 'lion', 'tiger', 'wolf', 'bear',
                       'elephant', 'fox', 'deer', 'rabbit', 'animal', 'pet']
    if any(word in prompt_lower for word in animal_keywords):
        enhancements.extend([
            "accurate animal anatomy",
            "realistic fur/feather texture",
            "natural animal proportions",
            "proper animal features"
        ])
    
    # Detect superheroes/characters
    hero_keywords = ['superhero', 'hero', 'villain', 'costume', 'suit', 'armor', 'cape', 'mask']
    if any(word in prompt_lower for word in hero_keywords):
        enhancements.extend([
            "accurate costume details",
            "proper suit design",
            "heroic pose",
            "dynamic action stance"
        ])
    
    # Detect vehicles
    vehicle_keywords = ['car', 'truck', 'bike', 'motorcycle', 'vehicle', 'bus', 'train']
    if any(word in prompt_lower for word in vehicle_keywords):
        enhancements.extend([
            "accurate vehicle proportions",
            "proper wheel alignment",
            "realistic automotive details"
        ])
    
    # Detect architecture/buildings
    building_keywords = ['building', 'house', 'castle', 'tower', 'skyscraper', 'architecture']
    if any(word in prompt_lower for word in building_keywords):
        enhancements.extend([
            "accurate architectural proportions",
            "proper perspective",
            "realistic materials"
        ])
    
    # Detect landscapes/nature
    nature_keywords = ['landscape', 'mountain', 'forest', 'ocean', 'beach', 'nature', 'sky', 'sunset']
    if any(word in prompt_lower for word in nature_keywords):
        enhancements.extend([
            "natural lighting",
            "atmospheric perspective",
            "realistic terrain"
        ])
    
    return enhancements

# ===============================
# ULTRA QUALITY PROMPT ENGINEERING WITH WEB SEARCH
# ===============================
async def create_web_enhanced_prompt(prompt: str) -> tuple:
    """
    Search web for references and create enhanced prompt
    """
    # Search for visual references
    references = await search_visual_references(prompt)
    
    # Extract visual features from search results
    visual_features = extract_visual_features(references, prompt)
    
    # Base quality modifiers
    base_quality = [
        "masterpiece",
        "best quality",
        "ultra detailed",
        "8k resolution",
        "professional",
        "perfect composition"
    ]
    
    # Get intelligent enhancements
    smart_enhancements = analyze_prompt_intelligently(prompt)
    
    # Build final prompt with web-searched features
    components = [prompt]
    
    if visual_features:
        components.append(visual_features)
        print(f"🎯 Visual features: {visual_features[:100]}...")
    
    components.extend(base_quality[:4])
    components.extend(smart_enhancements[:4])
    
    final_prompt = ", ".join(components)
    
    # COMPREHENSIVE negative prompt
    negative_prompt = [
        # Anatomy issues
        "deformed", "distorted", "disfigured", "mutation", "mutated",
        "bad anatomy", "wrong anatomy", "extra limb", "missing limb",
        "extra fingers", "fused fingers", "too many fingers", "missing fingers",
        "malformed limbs", "disconnected limbs", "floating limbs",
        
        # Face issues
        "bad face", "ugly face", "deformed face", "disfigured face",
        "extra eyes", "missing eyes", "bad eyes", "crossed eyes",
        "asymmetric face", "uneven features", "bad mouth", "deformed mouth",
        
        # Quality issues
        "blurry", "blur", "pixelated", "low quality", "worst quality",
        "low resolution", "jpeg artifacts", "watermark", "text", "signature",
        
        # Character issues
        "wrong character", "different character", "inaccurate", "incorrect",
        
        # General issues
        "duplicate", "cloned", "gross", "weird", "bad proportions"
    ]
    
    return final_prompt, ", ".join(negative_prompt)

# ===============================
# SMART API CALL WITH RETRY
# ===============================
async def smart_query(session, model_config: dict, payload: dict) -> bytes:
    """
    Query with intelligent retry and error handling
    """
    model_url = f"https://router.huggingface.co/hf-inference/models/{model_config['name']}"
    
    for attempt in range(3):
        try:
            async with session.post(
                model_url,
                headers=HEADERS,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=200)
            ) as response:
                
                if response.status == 200:
                    return await response.read()
                
                elif response.status == 503:
                    print(f"  Model loading... waiting (attempt {attempt + 1}/3)")
                    await asyncio.sleep(20)
                    continue
                
                else:
                    error_text = await response.text()
                    print(f"  API Error ({response.status}): {error_text[:150]}")
                    return None
                    
        except asyncio.TimeoutError:
            print(f"  Timeout on attempt {attempt + 1}/3")
            if attempt < 2:
                await asyncio.sleep(5)
                continue
            return None
            
        except Exception as e:
            print(f"  Error: {str(e)[:100]}")
            return None
    
    return None

# ===============================
# MULTI-MODEL GENERATION WITH WEB SEARCH
# ===============================
async def generate_best_quality(prompt: str) -> bytes:
    """
    Generate using web-enhanced prompt
    """
    # Create web-enhanced prompt
    final_prompt, negative = await create_web_enhanced_prompt(prompt)
    
    print(f"\n📝 Original: {prompt}")
    print(f"✨ Enhanced: {final_prompt[:150]}...")
    print(f"🚫 Negative: {negative[:120]}...")
    
    async with aiohttp.ClientSession() as session:
        for model_config in MODELS:
            model_name = model_config['name']
            print(f"\n🎨 Attempting: {model_name}")
            
            payload = {
                "inputs": final_prompt,
                "parameters": {
                    "negative_prompt": negative,
                    "num_inference_steps": model_config['steps'],
                    "guidance_scale": model_config['guidance'],
                    "seed": randint(100000, 999999)
                }
            }
            
            image_bytes = await smart_query(session, model_config, payload)
            
            if image_bytes:
                print(f"✅ Success with {model_name}!")
                return image_bytes
            
            print(f"❌ Failed with {model_name}")
            await asyncio.sleep(3)
    
    return None

# ===============================
# ADVANCED POST-PROCESSING
# ===============================
def enhance_image(image_bytes: bytes) -> Image.Image:
    """
    Apply professional enhancements
    """
    try:
        img = Image.open(io.BytesIO(image_bytes))
        img = Image.open(io.BytesIO(image_bytes))
        
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        from PIL import ImageEnhance, ImageFilter
        
        img = img.filter(ImageFilter.UnsharpMask(radius=1, percent=120, threshold=3))
        
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(1.1)
        
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.05)
        
        enhancer = ImageEnhance.Color(img)
        img = enhancer.enhance(1.05)
        
        return img
        
    except Exception as e:
        print(f"⚠️  Enhancement error: {e}")
        return Image.open(io.BytesIO(image_bytes)).convert('RGB')

# ===============================
# SAVE AND DISPLAY
# ===============================
def save_and_display(image: Image.Image, prompt: str):
    """
    Save with high quality and display
    """
    safe_name = "".join(c for c in prompt if c.isalnum() or c in (' ', '-', '_'))[:40]
    filename = safe_name.replace(' ', '_')
    
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    save_path = f"Data/Images/{filename}_{timestamp}.jpg"
    
    image.save(save_path, "JPEG", quality=98, optimize=True, subsampling=0)
    print(f"💾 Saved: {save_path}")
    
    try:
        image.show()
        sleep(3)
    except Exception as e:
        print(f"⚠️  Display error: {e}")

# ===============================
# MAIN PIPELINE
# ===============================
async def generate_image(prompt: str):
    """
    Complete generation pipeline with web search
    """
    print(f"\n{'='*70}")
    print(f"🎨 GENERATING: '{prompt}'")
    print(f"{'='*70}")
    
    # Generate with web-enhanced prompt
    image_bytes = await generate_best_quality(prompt)
    
    if not image_bytes:
        print("\n❌ All generation attempts failed")
        return False
    
    # Enhance
    print("\n✨ Enhancing image...")
    image = enhance_image(image_bytes)
    
    # Save and show
    save_and_display(image, prompt)
    
    print(f"\n{'='*70}")
    print("✅ GENERATION COMPLETE!")
    print(f"{'='*70}\n")
    
    return True

# ===============================
# WRAPPER (ORIGINAL FUNCTION NAME)
# ===============================
def GenerateImages(prompt: str):
    """
    Main function called by main.py
    """
    asyncio.run(generate_image(prompt))

# ===============================
# FILE WATCHER
# ===============================
if __name__ == "__main__":
    data_file = "Frontend/Files/ImageGeneration.data"
    
    Path("Frontend/Files").mkdir(parents=True, exist_ok=True)
    if not os.path.exists(data_file):
        with open(data_file, "w") as f:
            f.write("False,False")
    
    print("🚀 Image Generation Service Started (Web-Enhanced)")
    print("👀 Watching for requests...\n")
    
    while True:
        try:
            with open(data_file, "r") as f:
                data = f.read().strip()

            parts = data.split(",")
            if len(parts) != 2:
                sleep(1)
                continue

            prompt, status = parts[0].strip(), parts[1].strip()

            if status == "True":
                with open(data_file, "w") as f:
                    f.write("False,False")

                GenerateImages(prompt)
            else:
                sleep(1)

        except FileNotFoundError:
            with open(data_file, "w") as f:
                f.write("False,False")
            sleep(1)
            
        except Exception as e:
            print(f"❌ Error: {e}")
            sleep(2)
