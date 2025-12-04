-- Migration: Move credits from user table to user_credits table
-- Run this script to complete the database refactoring

-- Step 1: Create user_credits table
CREATE TABLE IF NOT EXISTS user_credits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL UNIQUE REFERENCES "user"(id) ON DELETE CASCADE,
    credits INTEGER NOT NULL DEFAULT 10
);

-- Step 2: Migrate existing credits data from user table to user_credits table
-- This creates a user_credits record for each existing user with their current credits value
INSERT INTO user_credits (user_id, credits)
SELECT id, COALESCE(credits, 10)
FROM "user"
WHERE id NOT IN (SELECT user_id FROM user_credits)
ON CONFLICT (user_id) DO NOTHING;

-- Step 3: Set default credits for any users that don't have credits set (shouldn't happen, but safe)
INSERT INTO user_credits (user_id, credits)
SELECT id, 10
FROM "user"
WHERE id NOT IN (SELECT user_id FROM user_credits)
ON CONFLICT (user_id) DO NOTHING;

-- Step 4: Drop the credits column from the user table
ALTER TABLE "user" DROP COLUMN IF EXISTS credits;

-- Verification queries (optional - uncomment to verify migration)
-- SELECT u.id, u.email, uc.credits
-- FROM "user" u
-- LEFT JOIN user_credits uc ON u.id = uc.user_id;
