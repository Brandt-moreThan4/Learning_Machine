

-- Add a boolean column to the quizzes table to indicate if the email has been sent
ALTER TABLE quiz_app.quizzes ADD COLUMN email_sent BOOLEAN NOT NULL DEFAULT FALSE;