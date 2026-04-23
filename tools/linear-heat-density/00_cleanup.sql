--
-- Cleanup and initialize output schema
-- Drops the schema defined by {output_schema} if it exists, then creates a new empty schema.
-- Usage: Replaces {output_schema} with the target schema name defined by format_params before execution.
--
-- DROP SCHEMA IF EXISTS {output_schema} CASCADE ;
-- CREATE SCHEMA {output_schema};

CREATE SCHEMA IF NOT EXISTS {output_schema};
DROP TABLE IF EXISTS {output_schema}.{output_table};