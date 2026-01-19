"""
Authentication callback for Chainlit
Database-backed authentication with password hashing
"""
import chainlit as cl
import asyncpg
import os
import hashlib
from typing import Optional


<<<<<<< HEAD
=======
def hash_password(password: str) -> str:
    """Hash a password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()


async def get_user_from_db(username: str) -> Optional[dict]:
    """
    Retrieve user from database
    
    Args:
        username: User's username
        
    Returns:
        User data dict or None
    """
    db_url = os.getenv(
        "CHAINLIT_POSTGRES_URL",
        "postgresql://chainlit:chainlit_password@localhost:5434/chainlit_db"
    ).replace("postgresql+asyncpg://", "postgresql://")
    
    try:
        conn = await asyncpg.connect(db_url)
        row = await conn.fetchrow(
            "SELECT identifier, metadata FROM users WHERE identifier = $1",
            username
        )
        await conn.close()
        
        if row:
            import json
            return {
                "identifier": row["identifier"],
                "metadata": json.loads(row["metadata"]) if row["metadata"] else {}
            }
    except Exception as e:
        print(f"❌ Database error: {e}")
    
    return None
>>>>>>> 4d35196 (feat: add user management script with user creation and listing functionality)


@cl.password_auth_callback
async def auth_callback(username: str, password: str) -> Optional[cl.User]:
    """
    Authenticate user with username and password from database
    
    Args:
        username: User's username
        password: User's password
        
    Returns:
        cl.User object if authentication successful, None otherwise
    """
    print(f"🔐 Authentication attempt for user: {username}")
    
    # Get user from database
    user_data = await get_user_from_db(username)
    
    if not user_data:
        print(f"❌ User '{username}' not found")
        return None
    
    # Verify password hash
    stored_password_hash = user_data["metadata"].get("password_hash")
    if not stored_password_hash or hash_password(password) != stored_password_hash:
        print(f"❌ Invalid password for user '{username}'")
        return None
    
    print(f"✅ User '{username}' authenticated successfully")
    
    # Return User object with metadata (without password hash)
    metadata = {k: v for k, v in user_data["metadata"].items() if k != "password_hash"}
    
    return cl.User(
        identifier=username,
        metadata=metadata
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
