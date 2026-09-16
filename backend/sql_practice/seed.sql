INSERT INTO domains (name) VALUES ('Physical'), ('Educational'), ('Mental Wellness'), ('Emotional'), ('Career');

INSERT INTO users (username, email) VALUES
('aditya', 'aditya@example.com'),
('riya', 'riya@example.com'),
('sam', 'sam@example.com');

INSERT INTO quests (title, domain_id, difficulty, xp_reward) VALUES
('30 min walk', 1, 'easy', 10),
('Read 10 pages', 2, 'easy', 10),
('Solve 5 LeetCode problems', 2, 'hard', 50),
('10 min meditation', 3, 'easy', 10),
('Journal for 5 minutes', 4, 'easy', 10),
('Update resume', 5, 'medium', 30);

INSERT INTO quest_completions (user_id, quest_id) VALUES
(1, 1), (1, 3), (1, 4),
(2, 2), (2, 4), (2, 5),
(3, 1), (3, 6);