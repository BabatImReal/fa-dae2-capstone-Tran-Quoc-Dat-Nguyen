# User Management

Users are now stored in the PostgreSQL database with hashed passwords, not in the code.

## Creating Users

Use the `scripts/create_user.py` script:

```bash
# Create a user
uv run python scripts/create_user.py <username> <password> "<display_name>" [role]

# Examples
uv run python scripts/create_user.py admin admin123 "Admin User" admin
uv run python scripts/create_user.py john pass123 "John Doe" user
```

## Listing Users

```bash
uv run python scripts/create_user.py list
```

## Default Users

Three default users have been created:

| Username | Password | Role  | Display Name  |
|----------|----------|-------|---------------|
| admin    | admin123 | admin | Admin User    |
| user     | user123  | user  | Regular User  |
| demo     | demo123  | user  | Demo User     |

## Security Notes

- Passwords are hashed using SHA-256
- Never commit user credentials to version control
- The database contains the hashed passwords, not plain text
- Change default passwords in production
- User data is stored in PostgreSQL at `localhost:5434`

## Database

Users are stored in the `users` table with:
- `identifier`: Username (unique)
- `metadata`: JSON containing:
  - `password_hash`: Hashed password
  - `display_name`: User's display name
  - `role`: User role (admin/user)
  - `provider`: Authentication provider (credentials)
