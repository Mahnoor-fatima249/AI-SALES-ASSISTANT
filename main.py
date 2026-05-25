import json, uvicorn, re
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
from agent import get_ai_response

app = FastAPI()
seen_images = {}
chat_histories = {}
pending_orders = {} # Ye track karega ke user ne order select kar liya hai

class ChatRequest(BaseModel):
    user_input: Optional[str] = ""
    sender_id: Optional[str] = "unknown"

@app.post("/chat")
async def chat_with_bot(request: ChatRequest):
    if request.sender_id not in chat_histories:
        chat_histories[request.sender_id] = []

    with open('stock.json', 'r') as f:
        inventory = json.load(f)

    # User input ko check karein ke kya wo "confirm" bol raha hai
    user_text = request.user_input.lower()
    
    # AI se response mangen
    reply = get_ai_response(request.user_input, inventory, chat_histories[request.sender_id])
    
    # Product dhoondhein
    found_item = next((item for item in inventory if item['name'].lower() in reply.lower() or item['name'].lower() in user_text), None)

    # Agar user ne product select kar liya hai, to usay pending_orders mein daal dein
    if found_item:
        pending_orders[request.sender_id] = found_item

    # ORDER CONFIRMATION LOGIC
    # Sirf tab confirm hoga agar user ne "confirm" bola ho aur order pending ho
    if "confirm" in user_text and request.sender_id in pending_orders:
        item = pending_orders[request.sender_id]
        receipt_text = f"✅ *Order Confirmed!*\n\n📜 *Order Receipt*\n🆔 ID: ORD-0031\n🛍️ Items: {item['name']}\n💰 Total: {item['price']} PKR\n\n💳 *Payment:* EasyPaisa/JazzCash: 0300-XXXXXXX\n\n📄 *Invoice:* http://127.0.0.1:8001/invoice/invoice_ORD-0031.pdf\n✨ Thank you! 😊"
        
        # Order ho gaya, ab pending list se hata dein
        del pending_orders[request.sender_id]
        
        return {
            "type": "text_image", 
            "reply": receipt_text, 
            "image_url": item['image_url'],
            "is_order": True
        }

    # NORMAL IMAGE LOGIC (Agar sirf product pucha hai)
    clean_reply = re.sub(r'https?://\S+', '', reply).strip()
    chat_histories[request.sender_id].extend([{"role": "user", "content": request.user_input}, {"role": "assistant", "content": reply}])

    if found_item:
        session_key = f"{request.sender_id}_{found_item['name']}"
        if session_key not in seen_images:
            seen_images[session_key] = True
            return {"type": "text_image", "reply": clean_reply, "image_url": found_item['image_url']}

    return {"type": "text", "reply": clean_reply}

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8001)