# Chainlit Authentication

## Default Login Credentials

The app has 3 pre-configured users for testing:

### Admin Account
- **Username:** `admin`
- **Password:** `admin123`
- **Role:** Admin

### Regular User Account
- **Username:** `user`
- **Password:** `user123`
- **Role:** User

### Demo Account
- **Username:** `demo`
- **Password:** `demo123`
- **Role:** User

## Features

✅ **Persistent Conversations** - All chats are saved to SQLite database
✅ **User Sessions** - Each user has their own conversation history
✅ **Resume Chats** - Access past conversations from the sidebar
✅ **Secure Authentication** - Password-protected access

## How to Use

1. **Start Chainlit:**
   ```bash
   uv run chainlit run ai-agent/core/chainlit_app.py -w
   ```

2. **Login:**
   - Open http://localhost:8000
   - Enter username and password
   - Click Login

3. **Access Past Conversations:**
   - Click the sidebar icon (📋)
   - Browse your conversation history
   - Click any thread to resume

## Database

Conversations are stored in `chainlit.db` (SQLite database) in the project root.

## Adding New Users

Edit `ai-agent/core/auth.py` and add users to the `USERS` dictionary:

```python
USERS = {
    "newuser": {
        "password": "password123",
        "display_name": "New User Name",
        "role": "user"
    }
}
```

## Production Deployment

For production, replace the simple password authentication with:
- OAuth (GitHub, Google, etc.)
- LDAP/Active Directory
- Database-backed user management
- Hashed passwords

See Chainlit documentation: https://docs.chainlit.io/authentication/overview
