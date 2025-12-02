CREATE DATABASE IF NOT EXISTS quizpay_db;
USE quizpay_db;

-- USERS TABLE
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(100) UNIQUE,
    password VARCHAR(255),
    wallet INT DEFAULT 0
);

-- QUIZ QUESTIONS TABLE
CREATE TABLE IF NOT EXISTS quiz (
    id INT AUTO_INCREMENT PRIMARY KEY,
    question TEXT,
    option1 VARCHAR(255),
    option2 VARCHAR(255),
    option3 VARCHAR(255),
    option4 VARCHAR(255),
    answer VARCHAR(100),
    amount INT
);


-- Insert sample questions
INSERT INTO quiz (question, option1, option2, option3, option4, answer, amount) VALUES
('2 + 2 = ?', '3', '4', '5', '6', '4', 10),
('Capital of India?', 'Delhi', 'Mumbai', 'Pune', 'Nagpur', 'Delhi', 15);
