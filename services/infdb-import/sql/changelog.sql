DROP TABLE IF EXISTS public.changelog CASCADE;
CREATE TABLE IF NOT EXISTS  public.changelog (
    id          BIGSERIAL PRIMARY KEY,
    tool        TEXT,
    modified_at TIMESTAMPTZ DEFAULT NOW(),
    comment     TEXT,
    modified_by TEXT,
    ags         TEXT,
    process_id  BIGINT
);

CREATE OR REPLACE FUNCTION public.fn_begin_changelog(
    p_tool TEXT,
    p_comment TEXT DEFAULT NULL,
    p_modified_by TEXT DEFAULT NULL,
    p_ags TEXT DEFAULT NULL,
    p_process_id BIGINT DEFAULT NULL
)
RETURNS BIGINT AS $$
DECLARE
    v_changelog_id BIGINT;
BEGIN
    INSERT INTO public.changelog (
        tool,
        modified_at,
        comment,
        modified_by,
        ags,
        process_id
    )
    VALUES (
        p_tool,
        NOW(),
        p_comment,
        p_modified_by,
        p_ags,
        p_process_id
    )
    RETURNING id INTO v_changelog_id;

    RETURN v_changelog_id;
END;
$$ LANGUAGE plpgsql;