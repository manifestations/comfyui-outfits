# OllamaPrompter.py
# A ComfyUI node that enhances prompts using Ollama's LLMs.
import requests
import json
import os
from .ethnic_outfit_common import CATEGORY

class OllamaPrompter:
    """
    A ComfyUI node that takes a comma-separated string of keywords,
    sends them to a local Ollama instance, and returns a descriptive,
    well-structured prompt for image generation.
    """
    
    # Helper to fetch installed models for dropdown
    @classmethod
    def get_installed_models(cls, ollama_url="http://127.0.0.1:11434/api/generate"):
        try:
            # IMPORTANT: The URL for fetching tags is /api/tags, not part of /api/generate
            tags_url = ollama_url.replace("/api/generate", "/api/tags")
            response = requests.get(tags_url, timeout=5)
            response.raise_for_status()
            data = response.json()
            # Return a list of model names. If empty, ComfyUI will show an empty dropdown.
            return [m["name"] for m in data.get("models", [])]
        except Exception as e:
            print(f"OllamaPrompter: Could not fetch installed models: {e}")
            # Return an empty list on error to prevent ComfyUI from crashing.
            # The dropdown will be empty, signaling a problem to the user.
            return []

    @classmethod
    def load_json_options(cls, filename):
        # Load from data/styles instead of styles
        styles_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'styles')
        path = os.path.join(styles_dir, filename)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"OllamaPrompter: Could not load {filename}: {e}")
            return []

    @classmethod
    def load_art_styles(cls):
        styles_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'styles')
        path = os.path.join(styles_dir, 'art_styles.json')
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)  # Return the full dict
        except Exception as e:
            print(f"OllamaPrompter: Could not load art_styles.json: {e}")
            return {}

    @staticmethod
    def load_prompt_instructions(style):
        prompts_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'prompts')
        filename = {
            'SDXL': 'sdxl.json',
            'Flux': 'flux.json',
        }.get(style.upper() if style else '', None)
        if not filename:
            return None
        path = os.path.join(prompts_dir, filename)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('instructions', None)
        except Exception as e:
            print(f"OllamaPrompter: Could not load prompt instructions for {style}: {e}")
            return None

    # Define the input types for the node
    @classmethod
    def INPUT_TYPES(cls):
        installed_models = cls.get_installed_models()
        # Load all dropdowns from data/styles (ignore poses and hair_style)
        cameras = ["random", "disabled"] + cls.load_json_options('cameras.json')
        films = ["random", "disabled"] + cls.load_json_options('film.json')
        movements = ["random", "disabled"] + cls.load_json_options('movements.json')
        art_styles_dict = cls.load_art_styles()
        art_styles = ["random", "disabled"] + list(art_styles_dict.keys())
        photographers = ["random", "disabled"] + cls.load_json_options('photographers.json')
        lighting = ["random", "disabled"] + cls.load_json_options('lighting.json')
        shot_types = ["random", "disabled"] + cls.load_json_options('shot_types.json')
        photography_types = ["random", "disabled"] + cls.load_json_options('photography_types.json')
        return {
            "required": {
                "keywords": ("STRING", {
                    "multiline": True,
                    "default": "a cat, sitting on a chair, fantasy art, epic, cinematic lighting"
                }),
                # LLM model dropdown: default is 'disabled', add a comment for highlighting
                "model_name": (["disabled"] + installed_models, {"default": "disabled", "description": "<b>LLM Model (REQUIRED for LLM prompt):</b>"}),
                "prompt_style": (["random", "disabled", "SDXL", "Flux"], {"default": "random"}),
                "photographer": (photographers, {"default": "random"}),
                "camera": (cameras, {"default": "random"}),
                "film": (films, {"default": "random"}),
                "movement": (movements, {"default": "random"}),
                "art_style": (art_styles, {"default": "random"}),
                "lighting": (lighting, {"default": "random"}),
                "shot_type": (shot_types, {"default": "random"}),
                "photography_type": (photography_types, {"default": "random"}),
                "override_instructions": ("BOOLEAN", {"default": False}),
                "custom_instructions": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "visible": "override_instructions"
                }),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
            },
            "optional": {
                "ollama_url": ("STRING", {
                    "default": "http://127.0.0.1:11434/api/generate"
                }),
            }
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("descriptive_prompt",)
    FUNCTION = "generate_prompt"
    CATEGORY = CATEGORY

    def generate_prompt(self, keywords, model_name, prompt_style, photographer, camera, film, movement, art_style, lighting, shot_type, photography_type, override_instructions, custom_instructions, seed, ollama_url="http://127.0.0.1:11434/api/generate"):
        if not keywords.strip():
            print("OllamaPrompter: No keywords provided. Returning empty string.")
            return ("",)
        # --- Seed validation and sanitization ---
        try:
            if isinstance(seed, str):
                seed = int(seed.strip()) if seed.strip() else 0
            elif not isinstance(seed, int):
                seed = 0
        except Exception:
            seed = 0
        # Compose extra options with prefixes
        extra = []
        if photographer and photographer not in ["disabled", "random"]: extra.append(f"photographer: {photographer}")
        if camera and camera not in ["disabled", "random"]: extra.append(f"camera: {camera}")
        if film and film not in ["disabled", "random"]: extra.append(f"film: {film}")
        if movement and movement not in ["disabled", "random"]: extra.append(f"movement: {movement}")
        if lighting and lighting not in ["disabled", "random"]: extra.append(f"lighting: {lighting}")
        if shot_type and shot_type not in ["disabled", "random"]: extra.append(f"shot type: {shot_type}")
        if photography_type and photography_type not in ["disabled", "random"]: extra.append(f"photography type: {photography_type}")
        # Use art_style description instead of name
        art_styles_dict = self.load_art_styles()
        if art_style and art_style not in ["disabled", "random"] and art_style in art_styles_dict:
            extra.append(f"art style: {art_styles_dict[art_style]}")
        prompt_full = keywords
        if extra:
            prompt_full = f"{keywords}, " + ", ".join(extra)
        print(f"OllamaPrompter: Contacting Ollama at {ollama_url} with model {model_name} and style {prompt_style}...")

        # Use custom instructions if override is enabled
        if override_instructions and custom_instructions.strip():
            instructions = custom_instructions.strip()
        else:
            # Handle random prompt_style
            styles = ["Flux", "SDXL"]
            style = prompt_style
            if style == "random":
                import random
                style = random.choice(styles)
            if style in styles:
                loaded_instructions = self.load_prompt_instructions(style)
                if loaded_instructions:
                    instructions = loaded_instructions
                else:
                    instructions = "Prompt instructions not found."
            else:
                instructions = ""
        # All old hardcoded elif/else blocks for prompt_style removed

        # This check is good, but now less critical at runtime since the dropdown ensures a valid model is selected
        # It's still good practice to keep it as a fallback.
        installed_models = self.get_installed_models(ollama_url)
        if not installed_models:
            error_message = "OllamaPrompter Error: No models found in Ollama. Please pull a model (e.g., 'ollama pull llama3')."
            print(error_message)
            return (f"ERROR: NO OLLAMA MODELS FOUND. Original keywords: {keywords}",)
        if model_name not in installed_models:
            print(f"OllamaPrompter: Model '{model_name}' not found. Using first installed model: {installed_models[0]}")
            model_name = installed_models[0]

        payload = {
            "model": model_name,
            "system": instructions,
            "prompt": prompt_full,
            "stream": False,
            "options": {
                "seed": seed
            }
        }

        try:
            response = requests.post(ollama_url, json=payload, timeout=60)
            response.raise_for_status()
            lines = response.text.strip().splitlines()
            response_json = json.loads(lines[-1])
            final_prompt = response_json.get("response", "").strip()
            # Clean up potential quotation marks from the LLM response
            if final_prompt.startswith('"') and final_prompt.endswith('"'):
                final_prompt = final_prompt[1:-1]
            if final_prompt.startswith("'") and final_prompt.endswith("'"):
                final_prompt = final_prompt[1:-1]
            print(f"OllamaPrompter: Received prompt: {final_prompt}")
            return (final_prompt,)
        except requests.exceptions.RequestException as e:
            error_message = f"OllamaPrompter Error: Could not connect to Ollama. Make sure Ollama is running and the URL is correct. Details: {e}"
            print(error_message)
            return (f"ERROR: OLLAMA NOT REACHABLE. Using original keywords: {keywords}",)
        except Exception as e:
            error_message = f"OllamaPrompter Error: An unexpected error occurred. {e}"
            print(error_message)
            return (f"ERROR: UNEXPECTED. Using original keywords: {keywords}",)

    def __call__(self, **kwargs):
        return self.generate_prompt(**kwargs)

NODE_CLASS_MAPPINGS = {
    "OllamaPrompter": OllamaPrompter
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "OllamaPrompter": "✨ Ollama Prompter"
}