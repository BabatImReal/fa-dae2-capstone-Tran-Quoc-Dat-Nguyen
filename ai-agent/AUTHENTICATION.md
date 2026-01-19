# Chainlit Authentication & User Management

## Default Login Credentials

The app has database-backed authentication with hashed passwords. Default users:

| Username | Password | Role  | Display Name  |
|----------|----------|-------|---------------|
| admin    | admin123 | admin | Admin User    |
| user     | user123  | user  | Regular User  |
| demo     | demo123  | user  | Demo User     |
| analyst  | analyst123 | user | Data Analyst |

⚠️ **Change these passwords in production!**

## Features

✅ **Database-Backed Authentication** - Users stored in PostgreSQL with SHA-256 hashed passwords  
✅ **Persistent Conversations** - All chats saved to PostgreSQL database  
✅ **User Sessions** - Each user has their own conversation history  
✅ **Resume Chats** - Access past conversations from the sidebar  
✅ **Secure Storage** - No credentials in code or version control  

## Quick Start

1. **Start Database:**
   ```bash
   docker-compose -f docker-compose-chainlit-db.yml up -d
   ```

2. **Start Chainlit:**
   ```bash
   uv run chainlit run ai-agent/chainlit/chainlit_app.py -w
   ```

3. **Login:**
   - Open http://localhost:8000
   - Enter username and password
   - Click Login

4. **Access Past Conversations:**
   - Click the sidebar icon (📋)
   - Browse your conversation history
   - Click any thread to resume

## User Management

### Creating Users

Use the `scripts/create_user.py` script:

```bash
# Create a user
uv run python scripts/create_user.py <username> <password> "<display_name>" [role]

# Examples
uv run python scripts/create_user.py admin admin123 "Admin User" admin
uv run python scripts/create_user.py john pass123 "John Doe" user
```

### Listing Users

```bash
uv run python scripts/create_user.py list
```

### Verifying Users in Database

```bash
docker exec chainlit-postgres psql -U chainlit -d chainlit_db -c "SELECT identifier, metadata->'display_name' as name, metadata->'role' as role FROM users;"
```

## Database Architecture

### User Storage
- **Location**: PostgreSQL on `localhost:5434`
- **Database**: `chainlit_db`
- **Table**: `users`

### User Table Schema
```sql
users (
    identifier VARCHAR UNIQUE,
    metadata JSONB,
    "createdAt" TIMESTAMP
)
```

### Metadata Structure
```json
{
  "password_hash": "240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9",
  "display_name": "Admin User",
  "role": "admin",
  "provider": "credentials"
}
```

### Conversation Storage
- **Tables**: `threads`, `steps`, `feedbacks`, `elements`
- **Data Layer**: SQLAlchemyDataLayer with asyncpg driver
- **Connection**: `postgresql+asyncpg://chainlit:chainlit_password@localhost:5434/chainlit_db`

## Security Features

### Password Hashing
- **Algorithm**: SHA-256
- **Implementation**: `hashlib.sha256(password.encode()).hexdigest()`
- **Storage**: Only hashes stored, never plain text
- **Verification**: Hash comparison on authentication

### Version Control Safety
- No passwords in code
- No user data in repository
- `.gitignore` configured to block:
  - `*.secret`
  - `*.password`
  - `users.json`
  - `credentials.json`

### Authentication Flow
1. User enters credentials in Chainlit UI
2. `auth_callback()` queries database by username
3. Password hashed with SHA-256
4. Hash compared with stored `password_hash`
5. User object returned with metadata (excluding password)

## Troubleshooting

### "Unable to sign in" Error

**Check if user exists:**
```bash
uv run python scripts/create_user.py list
```

**Recreate user with password hash:**
```bash
uv run python scripts/create_user.py admin admin123 "Admin User" admin
```

### Database Connection Failed

**Check database is running:**
```bash
docker ps | grep chainlit-postgres
```

**Restart database:**
```bash
docker-compose -f docker-compose-chainlit-db.yml restart
```

**View logs:**
```bash
docker logs chainlit-postgres
```

### Missing Password Hash

If users were created before password hashing was implemented, recreate them:
```bash
uv run python scripts/create_user.py <username> <password> "<display_name>" <role>
```

## Files Structure

```
ai-agent/
├── chainlit/
│   ├── chainlit_app.py      # Main application with auth
│   ├── auth.py               # Authentication functions
│   └── data_layer.py         # Custom data layer (legacy)
├── AUTHENTICATION.md         # This file
└── USER_MANAGEMENT.md        # (deprecated - merged into this file)

scripts/
└── create_user.py            # User management tool

docker-compose-chainlit-db.yml  # PostgreSQL database setup
```

## Production Recommendations

### 1. Change Default Passwords
```bash
uv run python scripts/create_user.py admin <strong-password> "Admin User" admin
```

### 2. Use Environment Variables
- Store database URL in `.env`
- Never commit `.env` to version control
- Use strong JWT secret: `CHAINLIT_AUTH_SECRET`

### 3. Upgrade Hashing Algorithm
Consider bcrypt or argon2 for production:
```python
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
```

### 4. Add Rate Limiting
- Prevent brute force attacks
- Implement login attempt tracking
- Lock accounts after failed attempts

### 5. Enable HTTPS
- Encrypt credentials in transit
- Use SSL/TLS certificates
- Configure reverse proxy (nginx/caddy)

### 6. Database Security
- Use strong database password
- Enable SSL for database connections
- Restrict database network access
- Regular backups

### 7. Advanced Authentication
For production, consider:
- OAuth (GitHub, Google, Azure AD)
- LDAP/Active Directory integration
- Multi-factor authentication (MFA)
- Single Sign-On (SSO)

See Chainlit documentation: https://docs.chainlit.io/authentication/overview

## Environment Variables

```bash
# Database
CHAINLIT_POSTGRES_URL=postgresql+asyncpg://chainlit:chainlit_password@localhost:5434/chainlit_db

# Authentication
CHAINLIT_AUTH_SECRET=super-secret-jwt-key-change-in-production

# OpenAI (for agent)
OPENAI_API_KEY=your-api-key
```

## Support

For issues or questions:
- Check terminal logs for error messages
- Verify database is running
- Ensure users have password hashes
- Review Chainlit documentation

