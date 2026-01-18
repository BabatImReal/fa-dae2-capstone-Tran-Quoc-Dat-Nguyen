-- Chainlit PostgreSQL initialization script
-- Creates tables for storing chat conversations, users, and related data

-- USERS
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    identifier TEXT NOT NULL,
    "createdAt" TEXT,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- THREADS
CREATE TABLE threads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT,
    "createdAt" TEXT,
    "userId" UUID,
    "userIdentifier" TEXT,
    tags TEXT[],
    metadata JSONB DEFAULT '{}'::jsonb
);

-- STEPS
CREATE TABLE steps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    "threadId" UUID REFERENCES threads(id) ON DELETE CASCADE,
    "parentId" UUID,
    name TEXT,
    type TEXT,
    input TEXT,
    output TEXT,
    "isError" BOOLEAN,
    streaming BOOLEAN,
    "waitForAnswer" BOOLEAN,
    "showInput" TEXT,
    "defaultOpen" BOOLEAN,
    "createdAt" TEXT NOT NULL,
    start TEXT,
    "end" TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    generation TEXT,
    tags TEXT[],
    language TEXT
);

-- FEEDBACKS
CREATE TABLE feedbacks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    "forId" UUID,
    value TEXT,
    comment TEXT
);

-- ELEMENTS
CREATE TABLE elements (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    "threadId" UUID,
    type TEXT,
    "chainlitKey" TEXT,
    url TEXT,
    "objectKey" TEXT,
    name TEXT,
    display TEXT,
    size TEXT,
    language TEXT,
    page TEXT,
    "forId" UUID,
    mime TEXT,
    props JSONB DEFAULT '{}'::jsonb
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_threads_user_id ON threads("userId");
CREATE INDEX IF NOT EXISTS idx_threads_user_identifier ON threads("userIdentifier");
CREATE INDEX IF NOT EXISTS idx_steps_thread_id ON steps("threadId");
CREATE INDEX IF NOT EXISTS idx_steps_parent_id ON steps("parentId");
CREATE INDEX IF NOT EXISTS idx_elements_thread_id ON elements("threadId");
CREATE INDEX IF NOT EXISTS idx_feedbacks_for_id ON feedbacks("forId");

-- Grant permissions to chainlit user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO chainlit;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO chainlit;

ALTER TABLE users OWNER TO chainlit;
ALTER TABLE threads OWNER TO chainlit;
ALTER TABLE steps OWNER TO chainlit;
ALTER TABLE feedbacks OWNER TO chainlit;
ALTER TABLE elements OWNER TO chainlit;

-- Grant default privileges for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO chainlit;
