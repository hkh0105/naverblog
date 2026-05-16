-- ============================================================
-- 병원 블로그 생성기 - Supabase PostgreSQL 스키마
-- Supabase Dashboard > SQL Editor에서 실행하세요.
-- ============================================================

-- 1. personas
CREATE TABLE IF NOT EXISTS personas (
    id BIGSERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    description TEXT NOT NULL,
    system_prompt TEXT NOT NULL,
    is_preset BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. generations
CREATE TABLE IF NOT EXISTS generations (
    id BIGSERIAL PRIMARY KEY,
    topic TEXT NOT NULL,
    persona_name TEXT NOT NULL,
    llm_model TEXT NOT NULL,
    post_type TEXT DEFAULT 'general',
    search_context TEXT,
    prompt_used TEXT NOT NULL,
    output_markdown TEXT NOT NULL,
    output_html TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    tags TEXT DEFAULT '[]'
);

-- 3. skills
CREATE TABLE IF NOT EXISTS skills (
    name TEXT PRIMARY KEY,
    enabled BOOLEAN DEFAULT TRUE,
    config TEXT DEFAULT '{}'
);

-- 4. app_config
CREATE TABLE IF NOT EXISTS app_config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

-- 5. blog_styles
CREATE TABLE IF NOT EXISTS blog_styles (
    key TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 6. blog_posts
CREATE TABLE IF NOT EXISTS blog_posts (
    post_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT '',
    content TEXT NOT NULL,
    pub_date TEXT,
    link TEXT,
    crawled_at TIMESTAMPTZ DEFAULT NOW()
);

-- 7. keyword_cache
CREATE TABLE IF NOT EXISTS keyword_cache (
    keyword TEXT NOT NULL,
    data_type TEXT NOT NULL,
    result_json TEXT NOT NULL,
    queried_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,
    PRIMARY KEY (keyword, data_type)
);

-- ============================================================
-- RLS (Row Level Security) 정책
-- service_role key 사용 시 RLS가 우회되므로 기본적으로 비활성화.
-- anon key를 사용할 경우 아래 주석을 해제하세요.
-- ============================================================

-- ALTER TABLE personas ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE generations ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE skills ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE app_config ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE blog_styles ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE blog_posts ENABLE ROW LEVEL SECURITY;

-- CREATE POLICY "Allow all for service role" ON personas FOR ALL USING (true);
-- CREATE POLICY "Allow all for service role" ON generations FOR ALL USING (true);
-- CREATE POLICY "Allow all for service role" ON skills FOR ALL USING (true);
-- CREATE POLICY "Allow all for service role" ON app_config FOR ALL USING (true);
-- CREATE POLICY "Allow all for service role" ON blog_styles FOR ALL USING (true);
-- CREATE POLICY "Allow all for service role" ON blog_posts FOR ALL USING (true);

-- ============================================================
-- 인덱스 (성능 최적화)
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_blog_posts_category ON blog_posts (category);
CREATE INDEX IF NOT EXISTS idx_generations_created_at ON generations (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_personas_is_preset ON personas (is_preset);
CREATE INDEX IF NOT EXISTS idx_keyword_cache_expires ON keyword_cache (expires_at);
