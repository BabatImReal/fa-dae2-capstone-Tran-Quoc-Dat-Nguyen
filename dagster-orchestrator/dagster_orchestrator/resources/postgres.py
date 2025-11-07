"""PostgreSQL database resource."""

import os
from typing import Any, Dict

import psycopg
from dagster import ConfigurableResource, InitResourceContext
from dotenv import load_dotenv
from pydantic import Field


class PostgresResource(ConfigurableResource):
    """Resource for PostgreSQL database connections."""
    
    host: str = Field(default="localhost", description="PostgreSQL host")
    port: int = Field(default=5432, description="PostgreSQL port")
    database: str = Field(default="postgres", description="Database name")
    user: str = Field(default="postgres", description="Database user")
    password: str = Field(default="", description="Database password")
    
    @classmethod
    def from_env(cls) -> "PostgresResource":
        """Create PostgresResource from environment variables."""
        load_dotenv()
        return cls(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            database=os.getenv("POSTGRES_DB", "postgres"),
            user=os.getenv("POSTGRES_USER", "postgres"),
            password=os.getenv("POSTGRES_PASSWORD", ""),
        )
    
    def get_connection(self) -> psycopg.Connection:
        """Get a PostgreSQL connection."""
        return psycopg.connect(
            host=self.host,
            port=self.port,
            dbname=self.database,
            user=self.user,
            password=self.password,
        )
    
    def get_credentials_dict(self) -> Dict[str, Any]:
        """Get credentials as a dictionary for dlt."""
        return {
            "drivername": "postgresql",
            "database": self.database,
            "username": self.user,
            "password": self.password,
            "host": self.host,
            "port": self.port,
        }
    
    def execute_query(self, query: str) -> Any:
        """Execute a SQL query and return results."""
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                try:
                    return cur.fetchall()
                except Exception:
                    return None
