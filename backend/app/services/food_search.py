"""Food search — combines USDA, Open Food Facts, and local Russian food DB."""
import logging
import aiohttp
from app.config import settings
from sqlalchemy import select, or_
from app.database import async_session, FoodItem

logger = logging.getLogger(__name__)


async def search_food(query: str, lang: str = "ru", limit: int = 20) -> list[dict]:
    """Search food across all sources."""
    results = []

    # 1. Search local DB first
    local = await _search_local(query, limit)
    results.extend(local)

    # 2. Search USDA if we have API key and need more results
    if len(results) < limit and settings.usda_api_key:
        usda = await _search_usda(query, limit - len(results))
        results.extend(usda)

    # 3. Search Open Food Facts
    if len(results) < limit:
        off = await _search_openfoodfacts(query, limit - len(results))
        results.extend(off)

    return results[:limit]


async def _search_local(query: str, limit: int) -> list[dict]:
    """Search local food database."""
    async with async_session() as session:
        q = query.lower()
        result = await session.execute(
            select(FoodItem).where(
                or_(
                    FoodItem.name_en.ilike(f"%{q}%"),
                    FoodItem.name_ru.ilike(f"%{q}%"),
                )
            ).limit(limit)
        )
        items = result.scalars().all()

    return [
        {
            "id": item.id,
            "name_en": item.name_en,
            "name_ru": item.name_ru,
            "source": item.source or "local",
            "calories_per_100g": item.calories_per_100g,
            "protein_per_100g": item.protein_per_100g,
            "carbs_per_100g": item.carbs_per_100g,
            "fat_per_100g": item.fat_per_100g,
            "serving_size_g": item.serving_size_g or 100,
            "image_url": item.image_url,
        }
        for item in items
    ]


async def _search_usda(query: str, limit: int) -> list[dict]:
    """Search USDA FoodData Central."""
    try:
        async with aiohttp.ClientSession() as client:
            async with client.get(
                "https://api.nal.usda.gov/fdc/v1/foods/search",
                params={
                    "api_key": settings.usda_api_key,
                    "query": query,
                    "pageSize": limit,
                    "dataType": "Foundation,SR Legacy",
                },
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status != 200:
                    return []
                data = await resp.json()

        results = []
        for food in data.get("foods", []):
            nutrients = {n["nutrientName"]: n.get("value", 0) for n in food.get("foodNutrients", [])}
            results.append({
                "name_en": food.get("description", ""),
                "name_ru": None,
                "source": "usda",
                "calories_per_100g": nutrients.get("Energy", 0),
                "protein_per_100g": nutrients.get("Protein", 0),
                "carbs_per_100g": nutrients.get("Carbohydrate, by difference", 0),
                "fat_per_100g": nutrients.get("Total lipid (fat)", 0),
                "serving_size_g": 100,
                "fdc_id": food.get("fdcId"),
            })
        return results
    except Exception as e:
        logger.error(f"USDA search failed: {e}")
        return []


async def _search_openfoodfacts(query: str, limit: int) -> list[dict]:
    """Search Open Food Facts."""
    try:
        async with aiohttp.ClientSession() as client:
            async with client.get(
                "https://world.openfoodfacts.org/cgi/search.pl",
                params={
                    "search_terms": query,
                    "search_simple": 1,
                    "action": "process",
                    "json": 1,
                    "page_size": limit,
                },
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status != 200:
                    return []
                data = await resp.json()

        results = []
        for product in data.get("products", []):
            nutriments = product.get("nutriments", {})
            name = product.get("product_name", "")
            if not name:
                continue
            results.append({
                "name_en": name,
                "name_ru": None,
                "source": "openfoodfacts",
                "calories_per_100g": nutriments.get("energy-kcal_100g", 0),
                "protein_per_100g": nutriments.get("proteins_100g", 0),
                "carbs_per_100g": nutriments.get("carbohydrates_100g", 0),
                "fat_per_100g": nutriments.get("fat_100g", 0),
                "serving_size_g": 100,
                "barcode": product.get("code"),
            })
        return results
    except Exception as e:
        logger.error(f"Open Food Facts search failed: {e}")
        return []


async def get_by_barcode(barcode: str) -> dict | None:
    """Look up food by barcode via Open Food Facts."""
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
            "name_en": product.get("product_name", ""),
            "source": "openfoodfacts",
            "barcode": barcode,
            "calories_per_100g": nutriments.get("energy-kcal_100g", 0),
            "protein_per_100g": nutriments.get("proteins_100g", 0),
            "carbs_per_100g": nutriments.get("carbohydrates_100g", 0),
            "fat_per_100g": nutriments.get("fat_100g", 0),
        }
    except Exception as e:
        logger.error(f"Barcode lookup failed: {e}")
        return None
