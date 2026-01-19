"""
User Management Script
Create users with hashed passwords in the database

Usage:
    python scripts/create_user.py admin admin123 "Admin User" admin
    python scripts/create_user.py user user123 "Regular User" user
"""
import asyncio
import asyncpg
import sys
import json
import os
import hashlib


def hash_password(password: str) -> str:
    """Hash a password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()


async def create_user(username: str, password: str, display_name: str, role: str = "user"):
    """Create a user in the database with hashed password"""
    
    # Hash the password
    password_hash = hash_password(password)
    
    # Database connection
    db_url = os.getenv(
        "CHAINLIT_POSTGRES_URL",
        "postgresql://chainlit:chainlit_password@localhost:5434/chainlit_db"
    )
    if db_url and "postgresql+asyncpg://" in db_url:
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
    
    try:
        conn = await asyncpg.connect(db_url)
        
        # Create user metadata
        metadata = {
            "password_hash": password_hash,
            "display_name": display_name,
            "role": role,
            "provider": "credentials"
        }
        
        # Insert or update user
        await conn.execute(
            """
            INSERT INTO users (identifier, metadata, "createdAt")
            VALUES ($1, $2, NOW())
            ON CONFLICT (identifier) 
            DO UPDATE SET metadata = $2
            """,
            username,
            json.dumps(metadata)
        )
        
        await conn.close()
        
        print(f"✅ User '{username}' created successfully!")
        print(f"   Display Name: {display_name}")
        print(f"   Role: {role}")
        
    except Exception as e:
        print(f"❌ Error creating user: {e}")
        sys.exit(1)


async def list_users():
    """List all users in the database"""
    
    db_url = os.getenv(
        "CHAINLIT_POSTGRES_URL"
    ).replace("postgresql+asyncpg://", "postgresql://")
    
    try:
        conn = await asyncpg.connect(db_url)
        
        rows = await conn.fetch(
            'SELECT identifier, metadata, "createdAt" FROM users ORDER BY "createdAt" DESC'
        )
        
        await conn.close()
        
        if not rows:
            print("No users found in database.")
            return
        
        print(f"\n📋 Users in database ({len(rows)} total):\n")
        print(f"{'Username':<20} {'Display Name':<30} {'Role':<10} {'Created'}")
        print("-" * 80)
        
        for row in rows:
            metadata = json.loads(row["metadata"]) if row["metadata"] else {}
            display_name = metadata.get("display_name", "N/A")
            role = metadata.get("role", "user")
            created = row["createdAt"] if isinstance(row["createdAt"], str) else row["createdAt"].strftime("%Y-%m-%d %H:%M")
            
            print(f"{row['identifier']:<20} {display_name:<30} {role:<10} {created}")
        
    except Exception as e:
        print(f"❌ Error listing users: {e}")
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) == 1 or sys.argv[1] == "list":
        # List users
        asyncio.run(list_users())
    elif len(sys.argv) >= 4:
        # Create user: username password display_name [role]
        username = sys.argv[1]
        password = sys.argv[2]
        display_name = sys.argv[3]
        role = sys.argv[4] if len(sys.argv) > 4 else "user"
        
        asyncio.run(create_user(username, password, display_name, role))
    else:
        print("Usage:")
        print("  Create user: python scripts/create_user.py <username> <password> <display_name> [role]")
        print("  List users:  python scripts/create_user.py list")
        print("\nExample:")
        print('  python scripts/create_user.py admin admin123 "Admin User" admin')
        sys.exit(1)
