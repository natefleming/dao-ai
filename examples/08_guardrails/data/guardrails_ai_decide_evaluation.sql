USE IDENTIFIER(:database);

-- Evaluation questions for guardrails_ai_decide.yaml. The evaluation pipeline
-- only generates questions from vector store documents, and this example has
-- none, so the questions are seeded here; generate-evaluation-data then sees
-- the table and skips generation.
CREATE TABLE IF NOT EXISTS guardrails_ai_decide_evaluation (
  request_id STRING COMMENT 'Scenario identifier'
  ,inputs STRUCT<messages: ARRAY<STRUCT<role: STRING, content: STRING>>> COMMENT 'Agent request'
  ,expectations STRUCT<expected_facts: ARRAY<STRING>> COMMENT 'Facts a good answer contains'
);
