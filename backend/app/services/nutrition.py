"""Nutrition calculation utilities."""


def calculate_bmr(weight_kg: float, height_cm: float, age: int, sex: str) -> float:
    """
    Mifflin-St Jeor BMR formula.

    Args:
        weight_kg: Body weight in kilograms.
        height_cm: Height in centimetres.
        age: Age in whole years.
        sex: "male" or "female" (any other value treated as female).

    Returns:
        Basal Metabolic Rate in kcal/day.
    """
    if sex == "male":
        return 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    return 10 * weight_kg + 6.25 * height_cm - 5 * age - 161


def calculate_tdee(bmr: float, activity_level: str) -> float:
    """
    Total Daily Energy Expenditure via the Harris-Benedict activity multiplier.

    Args:
        bmr: Basal Metabolic Rate (kcal/day) from calculate_bmr().
        activity_level: One of sedentary / light / moderate / active / very_active.
                        Defaults to "moderate" (×1.55) for unrecognised values.

    Returns:
        TDEE in kcal/day.
    """
    multipliers = {
        "sedentary": 1.2,
        "light": 1.375,
        "moderate": 1.55,
        "active": 1.725,
        "very_active": 1.9,
    }
    return bmr * multipliers.get(activity_level, 1.55)


def calculate_macros(target_calories: int, weight_kg: float, goal: str) -> dict:
    """
    Calculate daily macro-nutrient targets.

    Protein targets (g/kg body weight):
      - muscle:       2.0 g/kg  (high protein for muscle protein synthesis)
      - weight_loss:  1.8 g/kg  (preserve lean mass during deficit)
      - other:        1.6 g/kg  (general health recommendation)

    Fat is set at 25 % of total calories (÷ 9 kcal/g).
    Carbohydrates fill the remaining calorie budget.
    Water is estimated at 33 ml per kg body weight.

    Args:
        target_calories: Adjusted daily calorie target (from adjust_calories_for_goal).
        weight_kg: Body weight in kilograms.
        goal: weight_loss / muscle / flexibility / stress_relief / health or similar.

    Returns:
        Dict with keys: protein (g), carbs (g), fat (g), water_ml (ml).
    """
    if goal == "muscle":
        protein_g = int(weight_kg * 2.0)
    elif goal == "weight_loss":
        protein_g = int(weight_kg * 1.8)
    else:
        protein_g = int(weight_kg * 1.6)

    fat_g = int(target_calories * 0.25 / 9)
    carbs_g = int((target_calories - protein_g * 4 - fat_g * 9) / 4)
    # Guard against negative carbs in extreme edge cases
    carbs_g = max(0, carbs_g)

    water_ml = int(weight_kg * 33)

    return {
        "protein": protein_g,
        "carbs": carbs_g,
        "fat": fat_g,
        "water_ml": water_ml,
    }


def adjust_calories_for_goal(tdee: float, goal: str) -> int:
    """
    Adjust TDEE based on the user's fitness goal.

    Adjustments:
      - weight_loss:  −500 kcal/day (≈ 0.45 kg/week loss)
      - muscle:       +300 kcal/day (lean bulk surplus)
      - other goals:  TDEE maintained (no adjustment)

    Args:
        tdee: Total Daily Energy Expenditure in kcal/day.
        goal: weight_loss / muscle / flexibility / stress_relief / health or similar.

    Returns:
        Target daily calorie intake as a rounded integer.
    """
    if goal == "weight_loss":
        return int(tdee - 500)
    elif goal == "muscle":
        return int(tdee + 300)
    return int(tdee)
