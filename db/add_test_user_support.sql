-- ====================
-- TEST USER SUPPORT
-- ====================

-- Add test user support columns to users table
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS is_test_user BOOLEAN DEFAULT FALSE;
ALTER TABLE public.users ADD COLUMN IF NOT EXISTS expires_at TIMESTAMP WITH TIME ZONE;

-- Create index for test user queries
CREATE INDEX IF NOT EXISTS idx_users_test_user ON public.users(is_test_user) WHERE is_test_user = TRUE;
CREATE INDEX IF NOT EXISTS idx_users_expires_at ON public.users(expires_at) WHERE expires_at IS NOT NULL;

-- Function to check if a user is a test user
CREATE OR REPLACE FUNCTION public.is_test_user(user_id UUID)
RETURNS BOOLEAN AS $$
BEGIN
  RETURN EXISTS (
    SELECT 1 FROM public.users 
    WHERE id = user_id AND is_test_user = TRUE
  );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to clean up expired test users
CREATE OR REPLACE FUNCTION public.cleanup_expired_test_users()
RETURNS INTEGER AS $$
DECLARE
  deleted_count INTEGER;
BEGIN
  DELETE FROM public.users
  WHERE is_test_user = TRUE
    AND expires_at IS NOT NULL
    AND expires_at < NOW()
  RETURNING COUNT(*) INTO deleted_count;
  
  RETURN deleted_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Update RLS policies to handle test users appropriately
-- Test users should have limited access and be isolated

-- Drop existing policies to recreate with test user support
DROP POLICY IF EXISTS "Users can view own profile" ON public.users;
DROP POLICY IF EXISTS "Users can update own profile" ON public.users;

-- Recreate policies with test user considerations
CREATE POLICY "Users can view own profile" ON public.users
  FOR SELECT USING (
    auth.uid() = id OR 
    -- Allow service role to view all test users
    (is_test_user = TRUE AND auth.jwt()->>'role' = 'service_role')
  );

CREATE POLICY "Users can update own profile" ON public.users
  FOR UPDATE USING (
    auth.uid() = id AND 
    -- Prevent test users from modifying certain fields
    (is_test_user = FALSE OR auth.jwt()->>'role' = 'service_role')
  );

-- Add service role policies for test user management
CREATE POLICY "Service role can insert test users" ON public.users
  FOR INSERT WITH CHECK (
    auth.jwt()->>'role' = 'service_role' AND is_test_user = TRUE
  );

CREATE POLICY "Service role can delete test users" ON public.users
  FOR DELETE USING (
    auth.jwt()->>'role' = 'service_role' AND is_test_user = TRUE
  );

-- Update trigger to handle test user metadata
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.users (id, email, full_name, avatar_url, is_test_user, expires_at)
  VALUES (
    NEW.id,
    NEW.email,
    NEW.raw_user_meta_data->>'full_name',
    NEW.raw_user_meta_data->>'avatar_url',
    COALESCE((NEW.raw_user_meta_data->>'is_test_user')::BOOLEAN, FALSE),
    -- Set expiration for test users
    CASE 
      WHEN (NEW.raw_user_meta_data->>'is_test_user')::BOOLEAN = TRUE 
      THEN NOW() + INTERVAL '1 hour' * COALESCE((NEW.raw_user_meta_data->>'ttl_hours')::INTEGER, 1)
      ELSE NULL
    END
  );
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Add test mode support for projects and tasks
ALTER TABLE public.projects ADD COLUMN IF NOT EXISTS is_test_data BOOLEAN DEFAULT FALSE;
ALTER TABLE public.tasks ADD COLUMN IF NOT EXISTS is_test_data BOOLEAN DEFAULT FALSE;

-- Update RLS policies for projects to handle test data
DROP POLICY IF EXISTS "Users can view own projects" ON public.projects;
DROP POLICY IF EXISTS "Users can insert own projects" ON public.projects;
DROP POLICY IF EXISTS "Users can update own projects" ON public.projects;
DROP POLICY IF EXISTS "Users can delete own projects" ON public.projects;

CREATE POLICY "Users can view own projects" ON public.projects
  FOR SELECT USING (
    auth.uid() = user_id AND
    -- Regular users cannot see test data
    (is_test_data = FALSE OR EXISTS (
      SELECT 1 FROM public.users 
      WHERE id = auth.uid() AND is_test_user = TRUE
    ))
  );

CREATE POLICY "Users can insert own projects" ON public.projects
  FOR INSERT WITH CHECK (
    auth.uid() = user_id AND
    -- Test users can only create test data
    (is_test_data = EXISTS (
      SELECT 1 FROM public.users 
      WHERE id = auth.uid() AND is_test_user = TRUE
    ))
  );

CREATE POLICY "Users can update own projects" ON public.projects
  FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own projects" ON public.projects
  FOR DELETE USING (auth.uid() = user_id);

-- Update RLS policies for tasks to handle test data
DROP POLICY IF EXISTS "Users can view own tasks" ON public.tasks;
DROP POLICY IF EXISTS "Users can insert own tasks" ON public.tasks;
DROP POLICY IF EXISTS "Users can update own tasks" ON public.tasks;
DROP POLICY IF EXISTS "Users can delete own tasks" ON public.tasks;

CREATE POLICY "Users can view own tasks" ON public.tasks
  FOR SELECT USING (
    auth.uid() = user_id AND
    -- Regular users cannot see test data
    (is_test_data = FALSE OR EXISTS (
      SELECT 1 FROM public.users 
      WHERE id = auth.uid() AND is_test_user = TRUE
    ))
  );

CREATE POLICY "Users can insert own tasks" ON public.tasks
  FOR INSERT WITH CHECK (
    auth.uid() = user_id AND
    -- Test users can only create test data
    (is_test_data = EXISTS (
      SELECT 1 FROM public.users 
      WHERE id = auth.uid() AND is_test_user = TRUE
    ))
  );

CREATE POLICY "Users can update own tasks" ON public.tasks
  FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own tasks" ON public.tasks
  FOR DELETE USING (auth.uid() = user_id);

-- Function to mark all data from a test user as test data
CREATE OR REPLACE FUNCTION public.mark_test_user_data()
RETURNS TRIGGER AS $$
BEGIN
  -- Mark projects as test data if created by test user
  IF NEW.is_test_user = TRUE THEN
    UPDATE public.projects 
    SET is_test_data = TRUE 
    WHERE user_id = NEW.id;
    
    UPDATE public.tasks 
    SET is_test_data = TRUE 
    WHERE user_id = NEW.id;
  END IF;
  
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to mark test user data
CREATE TRIGGER mark_test_data_on_user_update
  AFTER UPDATE OF is_test_user ON public.users
  FOR EACH ROW
  WHEN (NEW.is_test_user = TRUE)
  EXECUTE FUNCTION public.mark_test_user_data();