"""
Authentication callback for Chainlit
Simple username/password authentication with user persistence
"""
import chainlit as cl
from typing import Optional




@cl.password_auth_callback
def auth_callback(username: str, password: str) -> Optional[cl.User]:
    """
    Authenticate user with username and password
    
    Args:
        username: User's username
        password: User's password
        
    Returns:
        cl.User object if authentication successful, None otherwise
    """
    print(f"🔐 Authentication attempt for user: {username}")
    
    # Check if user exists
    if username not in USERS:
        print(f"❌ User '{username}' not found")
        return None
    
    user_data = USERS[username]
    
    # Verify password
    if user_data["password"] != password:
        print(f"❌ Invalid password for user '{username}'")
        return None
    
    print(f"✅ User '{username}' authenticated successfully")
    
    # Return User object with metadata
    return cl.User(
        identifier=username,
        metadata={
            "role": user_data["role"],
            "display_name": user_data["display_name"],
            "provider": "credentials"
        }
    )


@cl.on_chat_start
async def on_auth_chat_start():
    """Called when an authenticated user starts a chat"""
    user = cl.user_session.get("user")
    if user:
        display_name = user.metadata.get("display_name", user.identifier)
        role = user.metadata.get("role", "user")
        
        await cl.Message(
            content=f"👋 Welcome back, **{display_name}**!\n\n"
                    f"Role: `{role}`\n"
                    f"User ID: `{user.identifier}`\n\n"
                    f"Your conversations are automatically saved and can be accessed anytime."
        ).send()
