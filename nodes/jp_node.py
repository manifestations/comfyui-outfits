from .ethnic_outfit_common import EthnicOutfitGenerator, CATEGORY
import os
import json

REGION_CODE = "jp"

# Load country info from common JSON
country_info = {"name": "Japanese", "flag": "🇯🇵"}
try:
    common_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'common', 'country_codes.json')
    with open(common_path, 'r', encoding='utf-8') as f:
        country_info = json.load(f)[REGION_CODE]
except Exception:
    pass

class JapaneseOutfitNode(EthnicOutfitGenerator):
    RETURN_TYPES = (
        "STRING",
        "INT",
    )
    RETURN_NAMES = (
        "description",
        "seed",
    )
    FUNCTION = "generate_description"
    CATEGORY = CATEGORY
    region_code = REGION_CODE

    @classmethod
    def IS_CHANGED(cls, **kwargs):
        return float("nan")

    def __init__(self, seed=None):
        super().__init__(REGION_CODE, seed)

NODE_CLASS_MAPPINGS = {
    "JapaneseOutfitNode": JapaneseOutfitNode
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "JapaneseOutfitNode": f'{country_info["flag"]} {country_info["name"]} Outfit'
}