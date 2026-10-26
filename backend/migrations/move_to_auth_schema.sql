-- Migration script to move users to a dedicated 'auth' schema

-- Create the auth schema
CREATE SCHEMA IF NOT EXISTS auth;

-- Move user_role and user_status types to auth schema if needed
-- Note: Moving types is tricky in some versions of Postgres, 
-- but we can just recreat them or leave them in public. 
-- For simplicity and reliability, we will move the table.

-- If users table exists in public, move it to auth
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'users') THEN
        ALTER TABLE public.users SET SCHEMA auth;
    END IF;
END $$;

-- Update the types if they are in public
DO $$ 
BEGIN
    -- We can't easily move types between schemas without potential issues in existing code.
    -- However, we can refer to them as public.user_role if needed.
    -- To be cleanest, let's keep the types in public but the table in auth.
END $$;
