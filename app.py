from flask import Flask, request, jsonify, send_from_directory
import os
import json
from bytez import Bytez

app = Flask(__name__)

BYTEZ_API_KEY = os.getenv("BYTEZ_API_KEY", "YOUR API")
MODEL_ID = "Qwen/Qwen3-4B-Instruct-2507"
sdk = Bytez(BYTEZ_API_KEY)
model = sdk.model(MODEL_ID)

def build_prompt(ingredients, cuisine=None, dietary_preferences=None, cooking_time=None):
    prompt = (
        "You are a world-class creative chef and culinary innovator.\n"
        "Treat all ingredients seriously and realistically. Do NOT make jokes, fantasy recipes, or playful names.\n"
        "If an ingredient is unusual, create a realistic recipe even if the ingredients are unreal like (dinosaur, extinct animals)—just create it.\n"
        "If an ingredient appears to be a misspelling of a real food, correct the spelling and use the correct ingredient in the recipe.\n" 
        "If you correct a spelling, mention the correction in the JSON output under a 'corrections' key.\n"
        "Your task is to create a simple, original, and delicious recipe using ONLY the provided ingredients.\n"
        "If something essential is missing (e.g., oil, salt, basic seasoning), improvise cleverly with what's available.\n"
        f"Ingredients: {', '.join(ingredients)}\n"
    )
    if cuisine:
        prompt += f"Cuisine style: {cuisine}\n"
    if dietary_preferences:
        prompt += f"Dietary preferences: {dietary_preferences}\n"
    if cooking_time:
        prompt += f"Maximum cooking time: {cooking_time} minutes\n"
    prompt += (
        "\nRespond ONLY with valid JSON, no extra text, in the following minimal format:\n"
        "{\n"
        '  "recipe_name": "string",\n'
        '  "ingredients": ["quantity + unit + ingredient"],\n'
        '  "instructions": ["step 1", "step 2", ...],\n'
        '  "enjoy": "string"\n'
        "}\n\n"
        "Example:\n"
        "{\n"
        '  \"recipe_name\": \"Creamy Garlic Pasta\",\n'
        '  \"ingredients\": [\n'
        '    \"200g spaghetti\",\n'
        '    \"2 tbsp olive oil\",\n'
        '    \"4 cloves garlic, minced\",\n'
        '    \"1 cup heavy cream\",\n'
        '    \"1/2 cup grated parmesan cheese\",\n'
        '    \"1 tsp salt\",\n'
        '    \"1/2 tsp black pepper\",\n'
        '    \"Fresh parsley for garnish\"\n'
        '  ],\n'
        '  \"instructions\": [\n'
        '    \"Cook spaghetti according to package instructions until al dente. Drain and set aside.\",\n'
        '    \"In a large skillet, heat olive oil over medium heat. Add minced garlic and sauté for 1–2 minutes until fragrant.\",\n'
        '    \"Pour in heavy cream and bring to a gentle simmer.\",\n'
        '    \"Stir in parmesan cheese until melted and smooth, then season with salt and pepper.\",\n'
        '    \"Add the cooked spaghetti to the sauce and toss until evenly coated.\",\n'
        '    \"Serve warm, garnished with chopped parsley and extra parmesan if desired.\"\n'
        '  ],\n'
        '  \"enjoy\": \"Enjoy your creamy garlic pasta — rich, comforting, and perfect for a quick weeknight dinner!\"\n'
        "}\n"
    )
    return prompt

def clean_json_response(content):
    content = content.strip()
    if content.startswith("```json"):
        content = content[7:]
    elif content.startswith("```"):
        content = content[3:]
    if content.endswith("```"):
        content = content[:-3]
    return content.strip()

@app.route("/")
def home():
    return send_from_directory(".", "index.html")

@app.route("/style.css")
def send_css():
    return send_from_directory(".", "style.css")

@app.route("/generate-recipe", methods=["POST"])
def generate_recipe():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data received. Please send JSON."}), 400

        ingredients = data.get("ingredients", [])
        cuisine = data.get("cuisine")
        dietary_preferences = data.get("dietary_preferences")
        cooking_time = data.get("cooking_time")

        if not ingredients or not isinstance(ingredients, list) or len(ingredients) < 2:
            return jsonify({"error": "Please provide at least 2 ingredients as a list."}), 400

        prompt = build_prompt(ingredients, cuisine, dietary_preferences, cooking_time)
        output, error = model.run([{"role": "user", "content": prompt}])
        if error:
            return jsonify({"error": f"Model error: {error}"}), 500

        content = clean_json_response(output["content"])
        recipe = json.loads(content)

        if not all(k in recipe for k in ["recipe_name", "ingredients", "instructions"]):
            return jsonify({"error": "Invalid recipe format from AI."}), 500

        return jsonify(recipe)

    except Exception as e:
        return jsonify({"error": f"Error processing request: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True)
