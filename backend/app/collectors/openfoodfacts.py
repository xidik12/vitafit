"""Open Food Facts collector — barcode scanning, halal labels."""
import logging
import aiohttp

logger = logging.getLogger(__name__)

async def lookup_barcode(barcode: str) -> dict | None:
    try:
        async with aiohttp.ClientSession() as client:
            async with client.get(
                f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json",
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
        if data.get("status") != 1:
            return None
        product = data.get("product", {})
        nutriments = product.get("nutriments", {})
        return {
            "name": product.get("product_name", ""),
            "barcode": barcode,
            "calories_per_100g": nutriments.get("energy-kcal_100g", 0),
            "protein_per_100g": nutriments.get("proteins_100g", 0),
            "carbs_per_100g": nutriments.get("carbohydrates_100g", 0),
            "fat_per_100g": nutriments.get("fat_100g", 0),
            "is_halal": _check_halal(product),
            "image_url": product.get("image_url"),
        }
    except Exception as e:
        logger.error(f"OFF barcode lookup error: {e}")
        return None

def _check_halal(product: dict) -> bool | None:
    labels = (product.get("labels_tags") or [])
    if "en:halal" in labels:
        return True
    ingredients = (product.get("ingredients_text") or "").lower()
    haram = {"pork", "lard", "gelatin", "alcohol", "wine", "beer"}
    for h in haram:
        if h in ingredients:
            return False
    return None  # Unknown
