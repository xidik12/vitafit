"""USDA FoodData Central collector."""
import logging
import aiohttp
from app.config import settings
from app.database import async_session, FoodItem
from sqlalchemy import select

logger = logging.getLogger(__name__)

async def search_usda(query: str, page_size: int = 25) -> list[dict]:
    if not settings.usda_api_key:
        return []
    try:
        async with aiohttp.ClientSession() as client:
            async with client.get(
                "https://api.nal.usda.gov/fdc/v1/foods/search",
                params={"api_key": settings.usda_api_key, "query": query, "pageSize": page_size, "dataType": "Foundation,SR Legacy"},
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status != 200:
                    return []
                data = await resp.json()
        results = []
        for food in data.get("foods", []):
            nutrients = {n["nutrientName"]: n.get("value", 0) for n in food.get("foodNutrients", [])}
            results.append({
                "fdc_id": food.get("fdcId"),
                "name": food.get("description", ""),
                "calories": nutrients.get("Energy", 0),
                "protein": nutrients.get("Protein", 0),
                "carbs": nutrients.get("Carbohydrate, by difference", 0),
                "fat": nutrients.get("Total lipid (fat)", 0),
            })
        return results
    except Exception as e:
        logger.error(f"USDA search error: {e}")
        return []
