-- Create CADS subset tables
-- Simplified version without DO blocks for compatibility

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create cads_researchers table
CREATE TABLE IF NOT EXISTS cads_researchers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    institution_id UUID NOT NULL REFERENCES institutions(id) ON DELETE CASCADE,
    openalex_id TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    h_index INTEGER,
    department TEXT,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Create indexes for cads_researchers
CREATE INDEX IF NOT EXISTS idx_cads_researchers_openalex_id ON cads_researchers(openalex_id);
CREATE INDEX IF NOT EXISTS idx_cads_researchers_institution_id ON cads_researchers(institution_id);
CREATE INDEX IF NOT EXISTS idx_cads_researchers_full_name ON cads_researchers(full_name);
CREATE INDEX IF NOT EXISTS idx_cads_researchers_h_index ON cads_researchers(h_index);

-- Create cads_works table
CREATE TABLE IF NOT EXISTS cads_works (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    researcher_id UUID NOT NULL REFERENCES cads_researchers(id) ON DELETE CASCADE,
    openalex_id TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    abstract TEXT,
    keywords TEXT,
    publication_year INTEGER,
    doi TEXT,
    citations INTEGER DEFAULT 0,
    embedding VECTOR(384),
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Create indexes for cads_works
CREATE INDEX IF NOT EXISTS idx_cads_works_openalex_id ON cads_works(openalex_id);
CREATE INDEX IF NOT EXISTS idx_cads_works_researcher_id ON cads_works(researcher_id);
CREATE INDEX IF NOT EXISTS idx_cads_works_publication_year ON cads_works(publication_year);
CREATE INDEX IF NOT EXISTS idx_cads_works_citations ON cads_works(citations);
CREATE INDEX IF NOT EXISTS idx_cads_works_title ON cads_works USING gin(to_tsvector('english', title));
CREATE INDEX IF NOT EXISTS idx_cads_works_abstract ON cads_works USING gin(to_tsvector('english', abstract));

-- Vector similarity index for embeddings
CREATE INDEX IF NOT EXISTS idx_cads_works_embedding ON cads_works USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Create cads_topics table
CREATE TABLE IF NOT EXISTS cads_topics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    work_id UUID NOT NULL REFERENCES cads_works(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    score FLOAT8,
    created_at TIMESTAMPTZ DEFAULT now()
);

-- Create indexes for cads_topics
CREATE INDEX IF NOT EXISTS idx_cads_topics_work_id ON cads_topics(work_id);
CREATE INDEX IF NOT EXISTS idx_cads_topics_name ON cads_topics(name);
CREATE INDEX IF NOT EXISTS idx_cads_topics_type ON cads_topics(type);
CREATE INDEX IF NOT EXISTS idx_cads_topics_score ON cads_topics(score);

-- Insert CADS researchers (matching by name patterns)
INSERT INTO cads_researchers (institution_id, openalex_id, full_name, h_index, department)
SELECT 
    r.institution_id,
    r.openalex_id,
    r.full_name,
    r.h_index,
    r.department
FROM researchers r
WHERE 
    -- Add name matching patterns here
    LOWER(r.full_name) LIKE '%xiangping%liu%' OR
    LOWER(r.full_name) LIKE '%danny%wescott%' OR
    LOWER(r.full_name) LIKE '%emanuel%alanis%' OR
    LOWER(r.full_name) LIKE '%karen%lewis%' OR
    LOWER(r.full_name) LIKE '%carolyn%chang%' OR
    LOWER(r.full_name) LIKE '%lucia%summers%' OR
    LOWER(r.full_name) LIKE '%maria%resendiz%' OR
    LOWER(r.full_name) LIKE '%jelena%tesic%' OR
    LOWER(r.full_name) LIKE '%gregory%lakomski%' OR
    LOWER(r.full_name) LIKE '%chiu%au%' OR
    LOWER(r.full_name) LIKE '%ivan%ojeda%' OR
    LOWER(r.full_name) LIKE '%young%ju%lee%' OR
    LOWER(r.full_name) LIKE '%chul%ho%lee%' OR
    LOWER(r.full_name) LIKE '%keshav%bhandari%' OR
    LOWER(r.full_name) LIKE '%vangelis%metsis%' OR
    LOWER(r.full_name) LIKE '%mylene%farias%' OR
    LOWER(r.full_name) LIKE '%ziliang%zong%' OR
    LOWER(r.full_name) LIKE '%apan%qasem%' OR
    LOWER(r.full_name) LIKE '%hyunhwan%kim%' OR
    LOWER(r.full_name) LIKE '%jie%zhu%' OR
    LOWER(r.full_name) LIKE '%yihong%yuan%' OR
    LOWER(r.full_name) LIKE '%barbara%hewitt%' OR
    LOWER(r.full_name) LIKE '%eunsang%cho%' OR
    LOWER(r.full_name) LIKE '%feng%wang%' OR
    LOWER(r.full_name) LIKE '%togay%ozbakkaloglu%' OR
    LOWER(r.full_name) LIKE '%semih%aslan%' OR
    LOWER(r.full_name) LIKE '%damian%valles%' OR
    LOWER(r.full_name) LIKE '%wenquan%dong%' OR
    LOWER(r.full_name) LIKE '%tongdan%jin%' OR
    LOWER(r.full_name) LIKE '%nadim%adi%' OR
    LOWER(r.full_name) LIKE '%francis%mendez%' OR
    LOWER(r.full_name) LIKE '%tahir%ekin%' OR
    LOWER(r.full_name) LIKE '%rasim%musal%' OR
    LOWER(r.full_name) LIKE '%dincer%konur%' OR
    LOWER(r.full_name) LIKE '%emily%zhu%' OR
    LOWER(r.full_name) LIKE '%xiaoxi%shen%' OR
    LOWER(r.full_name) LIKE '%monica%hughes%' OR
    LOWER(r.full_name) LIKE '%holly%lewis%' OR
    LOWER(r.full_name) LIKE '%denise%gobert%' OR
    LOWER(r.full_name) LIKE '%shannon%williams%' OR
    LOWER(r.full_name) LIKE '%subasish%das%' OR
    LOWER(r.full_name) LIKE '%sean%bauld%' OR
    LOWER(r.full_name) LIKE '%eduardo%perez%' OR
    LOWER(r.full_name) LIKE '%ty%schepis%' OR
    LOWER(r.full_name) LIKE '%larry%price%' OR
    LOWER(r.full_name) LIKE '%erica%nason%' OR
    LOWER(r.full_name) LIKE '%cindy%royal%' OR
    LOWER(r.full_name) LIKE '%david%gibbs%' OR
    LOWER(r.full_name) LIKE '%diane%dolozel%' OR
    LOWER(r.full_name) LIKE '%sarah%fritts%' OR
    LOWER(r.full_name) LIKE '%edwin%chow%' OR
    LOWER(r.full_name) LIKE '%li%feng%' OR
    LOWER(r.full_name) LIKE '%vishan%shen%' OR
    LOWER(r.full_name) LIKE '%holly%veselka%' OR
    LOWER(r.full_name) LIKE '%toni%watt%'
ON CONFLICT (openalex_id) DO NOTHING;

-- Insert CADS works (for the matched researchers)
INSERT INTO cads_works (researcher_id, openalex_id, title, abstract, keywords, publication_year, doi, citations, embedding)
SELECT 
    cr.id as researcher_id,
    w.openalex_id,
    w.title,
    w.abstract,
    w.keywords,
    w.publication_year,
    w.doi,
    w.citations,
    w.embedding
FROM works w
JOIN researchers r ON w.researcher_id = r.id
JOIN cads_researchers cr ON r.openalex_id = cr.openalex_id
ON CONFLICT (openalex_id) DO NOTHING;

-- Insert CADS topics (for the CADS works)
INSERT INTO cads_topics (work_id, name, type, score)
SELECT 
    cw.id as work_id,
    t.name,
    t.type,
    t.score
FROM topics t
JOIN works w ON t.work_id = w.id
JOIN researchers r ON w.researcher_id = r.id
JOIN cads_researchers cr ON r.openalex_id = cr.openalex_id
JOIN cads_works cw ON w.openalex_id = cw.openalex_id;

-- Create a view for easy querying
CREATE OR REPLACE VIEW cads_researcher_summary AS
SELECT 
    cr.id,
    cr.full_name,
    cr.department,
    cr.h_index,
    i.name as institution_name,
    COUNT(cw.id) as total_works,
    SUM(cw.citations) as total_citations,
    MAX(cw.publication_year) as latest_publication_year,
    COUNT(ct.id) as total_topics
FROM cads_researchers cr
JOIN institutions i ON cr.institution_id = i.id
LEFT JOIN cads_works cw ON cr.id = cw.researcher_id
LEFT JOIN cads_topics ct ON cw.id = ct.work_id
GROUP BY cr.id, cr.full_name, cr.department, cr.h_index, i.name
ORDER BY total_works DESC;

-- Show summary
SELECT 'CADS Migration Summary' as summary;
SELECT COUNT(*) as cads_researchers FROM cads_researchers;
SELECT COUNT(*) as cads_works FROM cads_works;
SELECT COUNT(*) as cads_topics FROM cads_topics;