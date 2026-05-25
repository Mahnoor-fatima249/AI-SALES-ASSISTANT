import json
import os
from groq import Groq
from dotenv import load_dotenv

# API Key load karein
load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def get_ai_response(user_message, inventory_data, chat_history):
    # Inventory ko text mein convert karein
    inv_text = json.dumps(inventory_data)
    
    # System Prompt (Strict Rules)
    system_prompt = f"""You are a professional Sales Assistant.
    Inventory: {inv_text}
    
    LANGUAGE RULE:
    1. Detect the user's language (Roman Urdu or English).
    2. Respond strictly in the same language as the user. Do NOT mix languages.
    
    CRITICAL RULES:
    1. If you mention a product, you MUST include its 'image_url' from the inventory in your response.
    2. Put the image link at the very end of your response.
    3. If the user wants to buy, you MUST finalize the order.
    4. To finalize, you MUST use the exact phrase: 'ORDER CONFIRMED'.
    5. If you do not say 'ORDER CONFIRMED', the system will NOT record the order.
    6. Be professional, polite, and brief."""

    # History aur Message prepare karein
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(chat_history)
    messages.append({"role": "user", "content": user_message})

    # Groq se fast response (Streaming mode ke liye logic)
    try:
        response = client.chat.completions.create(
            messages=messages,
            model="llama-3.3-70b-versatile", # Sab se fast model
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error in Groq API: {e}")
        return "Maazrat, filhal system busy hai. Thori der mein dobara koshish karein."