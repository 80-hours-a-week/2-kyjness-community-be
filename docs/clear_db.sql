-- puppytalk DB 데이터만 전부 비우기 (테이블 구조는 유지, AUTO_INCREMENT 초기화)
-- 사용: mysql -u root -p puppytalk < docs/clear_db.sql

USE puppytalk;

SET FOREIGN_KEY_CHECKS = 0;

TRUNCATE TABLE likes;
TRUNCATE TABLE post_images;
TRUNCATE TABLE comments;
TRUNCATE TABLE sessions;
TRUNCATE TABLE posts;
TRUNCATE TABLE images;
TRUNCATE TABLE users;

SET FOREIGN_KEY_CHECKS = 1;
