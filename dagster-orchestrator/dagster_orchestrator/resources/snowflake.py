"""Snowflake database resource."""

import os
from typing import Any, Dict

import snowflake.connector
from dagster import ConfigurableResource
from dotenv import load_dotenv
from pydantic import Field


class SnowflakeResource(ConfigurableResource):
    """Resource for Snowflake database connections."""
    
    account: str = Field(description="Snowflake account identifier")
    user: str = Field(description="Snowflake user")
    warehouse: str = Field(description="Snowflake warehouse")
    database: str = Field(description="Snowflake database")
    schema_name: str = Field(default="PUBLIC", description="Snowflake schema")
    role: str = Field(description="Snowflake role")
    authenticator: str = Field(default="SNOWFLAKE_JWT", description="Authentication method")
    private_key_file: str = Field(default="", description="Path to private key file")
    private_key_pwd: str = Field(default="", description="Private key password")
    
    @classmethod
    def from_env(cls) -> "SnowflakeResource":
        """Create SnowflakeResource from environment variables."""
        load_dotenv()
        return cls(
            account=os.getenv("SNOWFLAKE_ACCOUNT", ""),
            user=os.getenv("SNOWFLAKE_USER", ""),
            warehouse=os.getenv("SNOWFLAKE_WAREHOUSE", ""),
            database=os.getenv("SNOWFLAKE_DATABASE", ""),
            schema_name=os.getenv("SNOWFLAKE_SCHEMA", "PUBLIC"),
            role=os.getenv("SNOWFLAKE_ROLE", ""),
            authenticator=os.getenv("SNOWFLAKE_AUTHENTICATOR", "SNOWFLAKE_JWT"),
            private_key_file=os.getenv("SNOWFLAKE_PRIVATE_KEY_FILE_PATH", ""),
            private_key_pwd=os.getenv("SNOWFLAKE_PRIVATE_KEY_FILE_PWD", ""),
        )
    
    def get_connection(self) -> snowflake.connector.SnowflakeConnection:
        """Get a Snowflake connection."""
        from pathlib import Path
        
        kwargs = {
            "account": self.account,
            "user": self.user,
            "authenticator": self.authenticator,
            "warehouse": self.warehouse,
            "database": self.database,
            "schema": self.schema_name,
            "role": self.role,
        }
        
        if self.authenticator.upper() == "SNOWFLAKE_JWT":
            # Resolve private key file path
            private_key_path = self.private_key_file
            if private_key_path:
                key_path = Path(private_key_path)
                if not key_path.is_absolute():
                    # Assume relative to project root (3 levels up from this file)
                    project_root = Path(__file__).resolve().parents[3]
                    key_path = project_root / private_key_path
                
                # Convert to string with proper path separators
                private_key_path = str(key_path.resolve())
            
            kwargs.update({
                "private_key_file": private_key_path,
                "private_key_file_pwd": self.private_key_pwd,
            })
        
        return snowflake.connector.connect(**kwargs)
    
    def get_credentials_dict(self) -> Dict[str, Any]:
        """Get credentials as a dictionary for dlt."""
        credentials = {
            "database": self.database,
            "username": self.user,
            "host": self.account,
            "warehouse": self.warehouse,
            "role": self.role,
        }
        
        # Add private key authentication
        # dlt requires the private key content as a string
        if self.private_key_file:
            from pathlib import Path
            
            # Resolve path if relative
            key_path = Path(self.private_key_file)
            if not key_path.is_absolute():
                # Assume relative to project root (3 levels up from this file)
                project_root = Path(__file__).resolve().parents[3]
                key_path = project_root / self.private_key_file
            
            key_path = key_path.resolve()
            
            if key_path.exists():
                with open(key_path, 'rb') as f:
                    private_key_bytes = f.read()
                # dlt expects private key as string
                credentials["private_key"] = private_key_bytes.decode('utf-8')
                if self.private_key_pwd:
                    credentials["private_key_passphrase"] = self.private_key_pwd
            else:
                raise FileNotFoundError(f"Private key file not found: {key_path}")
        
        return credentials
    
    def execute_query(self, query: str) -> Any:
        """Execute a SQL query and return results."""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                try:
                    return cur.fetchall()
                except Exception:
                    return None
