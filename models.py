# Import BaseModel for schema definition
from pydantic import BaseModel
# Import List for type hinting arrays
from typing import List

# Define the schema for a diagnostic test result
class DiagnosticTest(BaseModel):
    # Name of the diagnostic test
    test_name: str
    # The actual value reported in the user's document
    patient_value: str
    # Reference range for the test
    value_range: str
    # Status of the result (exactly one of: "Low", "Normal", "High")
    status: str
    # Clinical severity score from 0 to 100 (0-33 implies Low, 34-66 implies Normal, 67-100 implies High)
    severity_score: int
    # Clinical interpretation of the result
    interpretation: str
    # Trend identifying if this biomarker degraded, improved, or is newly established
    trend: str

# Define the schema for a single food item within a meal
class MealItem(BaseModel):
    name: str # Name of the food/dish
    calories: int # Estimated calories
    protein: int # Grams of protein
    carbs: int # Grams of carbohydrates
    fats: int # Grams of fats
    water_ml: int # Milliliters of fluid/water content

# Define the schema for a single day's meal plan (used for each day of the week)
class DailyDayPlan(BaseModel):
    breakfast: List[MealItem]
    lunch: List[MealItem]
    dinner: List[MealItem]
    snacks: List[MealItem]

# Define the schema for meal options for a single day
class DailyMealOptions(BaseModel):
    meal_plan: DailyDayPlan

# Define the schema for a specific nutrient
class Nutrient(BaseModel):
    # Name of the required nutrient
    nutrient_name: str
    # Current status or need for the nutrient
    status: str 
    # Detailed description of why the nutrient is needed
    description: str

# Define the schema for a recommended food category
class FoodCategory(BaseModel):
    # Name of the food category
    category_name: str
    # Representative emoji for the category
    emoji: str
    # Example foods within this category
    examples: str

# Define the schema for foods that should be avoided
class AvoidedFood(BaseModel):
    # Name of the food to avoid
    food_name: str
    # Representative emoji for the hazard
    emoji: str
    # The clinical reason why this food should be avoided
    reason: str 

# Define the schema for exact, mathematically calculated daily macro-nutrients
class Macros(BaseModel):
    calories: int
    protein: int
    carbs: int
    fats: int

# Schema deprecated – replaced by weekly_plan lists

# Define the schema for grocery shopping lists
class GroceryCategory(BaseModel):
    # Name of the grocery section (e.g., Produce, Meat, Pantry)
    category_name: str
    # List of exact specific grocery items needed
    items: List[str]

from pydantic import BaseModel, Field

# Define the overall health profile schema
class HealthProfile(BaseModel):
    # Interactive Diet Adherence Score from 0 to 100
    health_score: int
    # List of diagnostic test analyses
    diagnostics: List[DiagnosticTest]
    # List of required nutrients
    nutrients: List[Nutrient]
    # List of recommended food categories
    foods: List[FoodCategory]
    # List of foods to strictly avoid
    avoided_foods: List[AvoidedFood]
    # Structured 7-Day Interactive Meal Calendar (Exactly 7 entries)
    weekly_meal_plan: List[DailyMealOptions] = Field(..., min_length=7, max_length=7, description="Strictly provide exactly 7 days representing Mon-Sun")
    # Exact mathematically calculated macro-nutrient targets
    daily_macros: Macros
    # Categorized weekly grocery shopping list
    grocery_list: List[GroceryCategory]
    # Recommended daily hydration goal
    hydration: str
