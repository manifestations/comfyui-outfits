import random
import json
import os
import re

CATEGORY = "🌀WizDroid/PromptGen"

class EthnicOutfitGenerator:
    def __init__(self, region_code, seed=None):
        self.region_code = region_code
        self.data_dir = os.path.join(os.path.dirname(__file__), "..", "data", region_code)
        self.seed = seed
        self.rng = random.Random(seed) if seed is not None else None
        # Load all relevant data files dynamically
        self.data = {}
        for fname in os.listdir(self.data_dir):
            if fname.endswith('.json'):
                key = fname.replace('.json', '')
                with open(os.path.join(self.data_dir, fname), 'r', encoding='utf-8') as f:
                    self.data[key] = json.load(f)
        # Load country info from common JSON
        self.country_info = {"name": region_code.upper(), "flag": ""}
        try:
            common_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'common', 'country_codes.json')
            with open(common_path, 'r', encoding='utf-8') as f:
                self.country_info = json.load(f).get(region_code, self.country_info)
        except Exception:
            pass

    def get_choice(self, input_str, default_choices):
        if input_str.lower() == "disabled":
            return ""
        elif input_str.lower() == "random":
            # Only pick from non-random, non-disabled options
            item_names = [c["name"] if isinstance(c, dict) else c for c in default_choices if c not in ("random", "disabled")]
            if not item_names:
                return ""
            if self.rng is not None:
                return self.rng.choice(item_names)
            else:
                return random.choice(item_names)
        else:
            return input_str

    def clean_description(self, description):
        description = re.sub(" +", " ", description)
        description = description.replace(" , ", ", ")
        description = description.replace("., ", ", ")
        description = description.strip()
        if description.endswith(","):
            description = description[:-1]
        return description

    @classmethod
    def INPUT_TYPES(cls):
        # This method is required by ComfyUI and must be a classmethod
        # It expects a class variable 'region_code' to be set in each subclass
        region_code = getattr(cls, 'region_code', None)
        if not region_code:
            raise ValueError("region_code must be set on the node class!")
        data_dir = os.path.join(os.path.dirname(__file__), "..", "data", region_code)
        styles_dir = os.path.join(os.path.dirname(__file__), "..", "data", "styles")
        def load_options(key, from_styles=False, append_common_poses=False, default_random=True, add_disabled=True):
            options = ["random"]
            if add_disabled:
                options.append("disabled")
            try:
                if from_styles:
                    with open(os.path.join(styles_dir, key + '.json'), 'r', encoding='utf-8') as f:
                        loaded = json.load(f)
                        if isinstance(loaded, list):
                            options += loaded
                else:
                    with open(os.path.join(data_dir, key + '.json'), 'r', encoding='utf-8') as f:
                        loaded = json.load(f)
                        if isinstance(loaded, list):
                            options += loaded
                # Append common poses if requested
                if append_common_poses and key == 'poses':
                    try:
                        with open(os.path.join(styles_dir, 'poses.json'), 'r', encoding='utf-8') as f:
                            common_poses = json.load(f)
                            if isinstance(common_poses, list):
                                for pose in common_poses:
                                    if pose not in options:
                                        options.append(pose)
                    except Exception:
                        pass
            except Exception:
                pass
            return options
        return {
            "required": {
                # Gender and age on top (no 'disabled')
                "gender": (["unisex", "male", "female", "transexual"], {"default": "random"}),
                "age": (["random", "infant", "young child", "older child", "teen", "young adult", "adult", "middle aged", "elderly"], {"default": "random"}),
                # Sorted head to toe, chest_clothing and artists removed
                "hair_style": (load_options('hair_styles', from_styles=True, add_disabled=True), {"default": "random"}),
                "head_gear": (load_options('head_gear', add_disabled=True), {"default": "random"}),
                "torso_clothing": (load_options('torso_clothing', add_disabled=False), {"default": "random"}),
                "arm_clothing": (load_options('arm_clothing', add_disabled=True), {"default": "random"}),
                "hand_accessories": (load_options('hand_accessories', add_disabled=True), {"default": "random"}),
                "jewelry": (load_options('jewelry', add_disabled=True), {"default": "random"}),
                "fabric_colors": (load_options('fabric_colors', add_disabled=True), {"default": "random"}),
                "leg_clothing": (load_options('leg_clothing', add_disabled=True), {"default": "random"}),
                "footwear": (load_options('footwear', add_disabled=True), {"default": "random"}),
                "pose": (load_options('poses', append_common_poses=True, add_disabled=True), {"default": "random"}),
                "detailed_description": (["enabled", "disabled"], {"default": "enabled"}),
                "trigger_word": ("STRING", {"default": ""}),
                "custom_text": ("STRING", {"default": ""}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
            }
        }

    def generate_description(self, **kwargs):
        seed = kwargs.get("seed", 0)
        # If seed is None, use unseeded randomness for true randomization
        if seed is not None:
            self.seed = seed
            self.rng = random.Random(seed)
        else:
            self.seed = None
            self.rng = None
        def getval(key, default):
            return kwargs.get(key, default)
        gender = getval("gender", "unisex")
        age = getval("age", "random")
        detailed = kwargs.get("detailed_description", "enabled") == "enabled"
        trigger_word = kwargs.get("trigger_word", "")
        custom_text = kwargs.get("custom_text", "")
        head_gear = self.get_choice(getval("head_gear", ""), self.data.get("head_gear", []))
        chest_clothing = self.get_choice(getval("chest_clothing", ""), self.data.get("chest_clothing", []))
        leg_clothing = self.get_choice(getval("leg_clothing", ""), self.data.get("leg_clothing", []))
        arm_clothing = self.get_choice(getval("arm_clothing", ""), self.data.get("arm_clothing", []))
        jewelry = self.get_choice(getval("jewelry", ""), self.data.get("jewelry", []))
        footwear = self.get_choice(getval("footwear", ""), self.data.get("footwear", []))
        hand_accessories = self.get_choice(getval("hand_accessories", ""), self.data.get("hand_accessories", []))
        fabric_colors = self.get_choice(getval("fabric_colors", ""), self.data.get("fabric_colors", []))
        torso_clothing = self.get_choice(getval("torso_clothing", ""), self.data.get("torso_clothing", []))
        hair_style = self.get_choice(getval("hair_style", ""), self.data.get("hair_styles", []))
        # Merge poses from region and common styles/poses.json
        poses = list(self.data.get("poses", []))
        common_poses_path = os.path.join(os.path.dirname(__file__), "..", "styles", "poses.json")
        if os.path.exists(common_poses_path):
            with open(common_poses_path, 'r', encoding='utf-8') as f:
                common_poses = json.load(f)
                poses.extend([p for p in common_poses if p not in poses])
        pose = self.get_choice(getval("pose", ""), poses)

        components = []
        if trigger_word:
            components.append(trigger_word)
            components.append(", ")
        if age and age != "random":
            components.append(f"{age} ")
        if gender and gender != "unisex":
            components.append(f"{gender} ")
        if detailed:
            if chest_clothing or torso_clothing:
                components.append("dressed in ")
        if chest_clothing:
            components.append(chest_clothing)
        if torso_clothing:
            if chest_clothing:
                components.append(" and ")
            components.append(torso_clothing)
        if leg_clothing:
            if chest_clothing or torso_clothing:
                components.append(" with ")
            components.append(leg_clothing)
        if arm_clothing:
            components.append(", sleeves: ")
            components.append(arm_clothing)
        if fabric_colors:
            components.append(f" in {fabric_colors}")
        if head_gear:
            components.append(", wearing ")
            components.append(head_gear)
        if jewelry:
            components.append(", adorned with ")
            components.append(jewelry)
        if hand_accessories:
            components.append(", featuring ")
            components.append(hand_accessories)
        if hair_style:
            components.append(f", hairstyle: {hair_style}")
        if footwear:
            components.append(", finished with ")
            components.append(footwear)
        if pose:
            if detailed:
                components.append(", ")
                components.append(pose)
            else:
                components = [pose]
        description = "".join(components)
        description = self.clean_description(description)
        if custom_text:
            description += ", " + custom_text
        return description, seed
