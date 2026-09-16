CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE domains (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE quests (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    domain_id INTEGER NOT NULL REFERENCES domains(id),
    difficulty TEXT CHECK (difficulty IN ('easy','medium','hard')),
    xp_reward INTEGER NOT NULL
);

CREATE TABLE quest_completions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    quest_id INTEGER NOT NULL REFERENCES quests(id),
    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);