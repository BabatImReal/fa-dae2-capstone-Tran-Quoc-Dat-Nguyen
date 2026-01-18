"""
Custom PostgreSQL Data Layer for Chainlit
Based on official Chainlit documentation
"""
import asyncpg
from typing import Optional, Dict, List
from chainlit.data import BaseDataLayer, queue_until_user_message
from chainlit.step import StepDict
from chainlit.user import User
from chainlit.element import ElementDict
import json
from datetime import datetime
import os


class PostgreSQLDataLayer(BaseDataLayer):
    """PostgreSQL implementation of Chainlit's data persistence layer"""
    
    def __init__(self):
        self.pool = None
        self.db_url = os.getenv("CHAINLIT_POSTGRES_URL")
        print(f"🔧 Data layer initialized with URL: {self.db_url}")
    
    async def init(self):
        """Initialize database connection pool"""
        if not self.pool:
            try:
                self.pool = await asyncpg.create_pool(self.db_url, min_size=2, max_size=10)
                print(f"✅ Connected to PostgreSQL database for persistence")
            except Exception as e:
                print(f"❌ Failed to connect to PostgreSQL: {e}")
    
    async def close(self):
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()
    
    async def get_user(self, identifier: str) -> Optional[User]:
        """Retrieve user by identifier"""
        print(f"🔍 Getting user: {identifier}")
        await self.init()
        if not self.pool:
            return None
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                'SELECT id, identifier, metadata FROM users WHERE identifier = $1',
                identifier
            )
            if row:
                return User(
                    identifier=row['identifier'],
                    metadata=json.loads(row['metadata']) if row['metadata'] else {}
                )
        return None
    
    async def create_user(self, user: User) -> Optional[User]:
        """Create a new user"""
        print(f"📝 Creating user: {user.identifier}")
        await self.init()
        if not self.pool:
            return user
        async with self.pool.acquire() as conn:
            await conn.execute(
                '''
                INSERT INTO users (identifier, "createdAt", metadata)
                VALUES ($1, $2, $3)
                ON CONFLICT (identifier) DO NOTHING
                ''',
                user.identifier,
                datetime.utcnow().isoformat(),
                json.dumps(user.metadata) if user.metadata else '{}'
            )
        print(f"✅ User {user.identifier} saved")
        return user
    
    async def update_thread(
        self,
        thread_id: str,
        name: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict] = None,
        tags: Optional[List[str]] = None
    ):
        """Update thread information"""
        print(f"📝 Creating thread: {thread_id} for user: {user_id}")
        await self.init()
        if not self.pool:
            return
        async with self.pool.acquire() as conn:
            await conn.execute(
                '''
                INSERT INTO threads (id, name, "createdAt", "userIdentifier", metadata, tags)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (id) DO UPDATE SET
                    name = COALESCE($2, threads.name),
                    metadata = COALESCE($5, threads.metadata),
                    tags = COALESCE($6, threads.tags)
                ''',
                thread_id,
                name,
                datetime.utcnow().isoformat(),
                user_id,
                json.dumps(metadata) if metadata else '{}',
                tags or []
            )
        print(f"✅ Thread saved")
    
    async def get_thread(self, thread_id: str) -> Optional[Dict]:
        """Retrieve thread by ID"""
        await self.init()
        if not self.pool:
            return None
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                'SELECT id, name, "userIdentifier", metadata, tags, "createdAt" FROM threads WHERE id = $1',
                thread_id
            )
            if row:
                return {
                    "id": str(row['id']),
                    "name": row['name'],
                    "userId": row['userIdentifier'],
                    "metadata": json.loads(row['metadata']) if row['metadata'] else {},
                    "tags": row['tags'] or [],
                    "createdAt": row['createdAt']
                }
        return None
    
    async def list_threads(self, pagination: Dict, filters: Dict) -> Dict:
        """List threads with pagination"""
        await self.init()
        if not self.pool:
            return {"data": [], "pageInfo": {"hasNextPage": False, "endCursor": None}}
        
        user_id = filters.get("userId")
        
        async with self.pool.acquire() as conn:
            query = 'SELECT id, name, "userIdentifier", metadata, tags, "createdAt" FROM threads'
            params = []
            if user_id:
                query += ' WHERE "userIdentifier" = $1'
                params.append(user_id)
            
            query += ' ORDER BY "createdAt" DESC LIMIT 50'
            
            rows = await conn.fetch(query, *params)
            
            threads = [
                {
                    "id": str(row['id']),
                    "name": row['name'],
                    "userId": row['userIdentifier'],
                    "metadata": json.loads(row['metadata']) if row['metadata'] else {},
                    "tags": row['tags'] or [],
                    "createdAt": row['createdAt']
                }
                for row in rows
            ]
            
            return {
                "data": threads,
                "pageInfo": {
                    "hasNextPage": False,
                    "endCursor": None
                }
            }
    
    async def delete_thread(self, thread_id: str):
        """Delete a thread"""
        await self.init()
        if not self.pool:
            return
        async with self.pool.acquire() as conn:
            await conn.execute('DELETE FROM threads WHERE id = $1', thread_id)
    
    @queue_until_user_message()
    async def create_step(self, step_dict: StepDict):
        """Create a new step (message)"""
        print(f"📝 Creating step: {step_dict.get('type')} in thread {step_dict.get('threadId')}")
        await self.init()
        if not self.pool:
            return
        async with self.pool.acquire() as conn:
            await conn.execute(
                '''
                INSERT INTO steps (
                    id, name, type, "threadId", "parentId", "createdAt",
                    input, output, metadata, "isError", "showInput"
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
                ON CONFLICT (id) DO UPDATE SET 
                    output = $8,
                    metadata = $9
                ''',
                step_dict.get("id"),
                step_dict.get("name"),
                step_dict.get("type"),
                step_dict.get("threadId"),
                step_dict.get("parentId"),
                datetime.utcnow().isoformat(),
                step_dict.get("input"),
                step_dict.get("output"),
                json.dumps(step_dict.get("metadata", {})),
                step_dict.get("isError", False),
                step_dict.get("showInput", "true")
            )
        print(f"✅ Step saved")
    
    async def update_step(self, step_dict: StepDict):
        """Update an existing step"""
        await self.create_step(step_dict)
    
    async def delete_step(self, step_id: str):
        """Delete a step"""
        await self.init()
        if not self.pool:
            return
        async with self.pool.acquire() as conn:
            await conn.execute('DELETE FROM steps WHERE id = $1', step_id)
    
    async def get_thread_author(self, thread_id: str) -> str:
        """Get the author of a thread"""
        await self.init()
        if not self.pool:
            return ""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                'SELECT "userIdentifier" FROM threads WHERE id = $1',
                thread_id
            )
            return row['userIdentifier'] if row else ""
    
    async def upsert_feedback(self, feedback: Dict) -> str:
        """Create or update feedback"""
        await self.init()
        if not self.pool:
            return ""
        feedback_id = feedback.get("id", str(datetime.utcnow().timestamp()))
        
        async with self.pool.acquire() as conn:
            await conn.execute(
                '''
                INSERT INTO feedbacks (id, "forId", value, comment)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (id) DO UPDATE SET value = $3, comment = $4
                ''',
                feedback_id,
                feedback.get("forId"),
                str(feedback.get("value")),
                feedback.get("comment")
            )
        return feedback_id
    
    async def delete_feedback(self, feedback_id: str) -> bool:
        """Delete feedback"""
        await self.init()
        if not self.pool:
            return False
        async with self.pool.acquire() as conn:
            await conn.execute('DELETE FROM feedbacks WHERE id = $1', feedback_id)
        return True
    
    async def create_element(self, element_dict: ElementDict):
        """Create an element"""
        pass
    
    async def get_element(self, thread_id: str, element_id: str) -> Optional[ElementDict]:
        """Get an element"""
        return None
    
    async def delete_element(self, element_id: str):
        """Delete an element"""
        pass
    
    async def delete_user_session(self, id: str) -> bool:
        """Delete a user session"""
        return True
    
    async def get_favorite_steps(self, user_id: str) -> List:
        """Get user's favorite steps"""
        return []
    
    def build_debug_url(self) -> str:
        """Build debug URL"""
        return "postgresql://localhost:5434/chainlit_db"
