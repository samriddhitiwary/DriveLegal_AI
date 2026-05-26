import os
import sys
import asyncio
import uuid
import logging
from dotenv import load_dotenv

# Load env variables
load_dotenv()

# Add current dir to path to resolve imports correctly
sys.path.append(os.path.dirname(__file__))

# Hide background RAG process logs during interactive chat to keep the conversation clean
logging.getLogger("drive_legal_ai").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("google_genai").setLevel(logging.WARNING)

from app.rag.chatbot import ask_chatbot

async def main():
    conversation_id = str(uuid.uuid4())
    
    print("=" * 65)
    print("       🚗  DRIVELEGAL AI - INTERACTIVE TERMINAL CHAT  🚗       ")
    print("=" * 65)
    print("Welcome! I am your conversational traffic law assistant.")
    print("I can help you answer questions based on official Maharashtra")
    print("and Tamil Nadu traffic regulations.")
    print("Type 'exit' or 'quit' to end the session.")
    print("=" * 65)
    print()

    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\nDriveLegal AI: Goodbye! Drive safely.")
            break

        if not user_input:
            continue

        if user_input.lower() in ["exit", "quit"]:
            print("\nDriveLegal AI: Goodbye! Drive safely.")
            break

        print("DriveLegal AI: Thinking...", end="\r", flush=True)
        
        # Call the conversational RAG chatbot engine
        response_text, sources = await ask_chatbot(user_input, conversation_id)
        
        # Clear the "Thinking..." line
        print(" " * 30, end="\r", flush=True)
        
        print(f"\nDriveLegal AI:\n{response_text}")
        
        if sources:
            print(f"\nSources: {', '.join(sources)}")
        print("-" * 65)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Error starting chat: {e}")
