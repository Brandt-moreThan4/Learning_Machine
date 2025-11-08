

-- Delete existing schema if needed
DROP SCHEMA IF EXISTS quiz_app CASCADE;

CREATE SCHEMA IF NOT EXISTS quiz_app;



CREATE TABLE IF NOT EXISTS quiz_app.quizzes (
  id VARCHAR(255) PRIMARY KEY,             
  data JSONB NOT NULL,                            
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
