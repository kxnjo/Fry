use `FryGames`;

-- -----------------------------------------------------
-- Table `review`
-- -----------------------------------------------------
ALTER TABLE `review`
DROP FOREIGN KEY `fk_review_game1`,
DROP FOREIGN KEY `fk_review_user1`;

ALTER TABLE `review`
ADD CONSTRAINT `fk_review_game1`
FOREIGN KEY (`game_id`) REFERENCES `game` (`game_id`)
ON DELETE CASCADE
ON UPDATE CASCADE,
ADD CONSTRAINT `fk_review_user1`
FOREIGN KEY (`user_id`) REFERENCES `user` (`user_id`)
ON DELETE CASCADE
ON UPDATE CASCADE;

-- -----------------------------------------------------
-- Table `price_change`
-- -----------------------------------------------------
ALTER TABLE `price_change`
DROP FOREIGN KEY `fk_price_change_game1`;

ALTER TABLE `price_change`
ADD CONSTRAINT `fk_price_change_game1`
FOREIGN KEY (`game_id`) REFERENCES `game` (`game_id`)
ON DELETE CASCADE
ON UPDATE CASCADE;

-- -----------------------------------------------------
-- Table `friend`
-- -----------------------------------------------------
ALTER TABLE `friend`
DROP FOREIGN KEY `fk_friend_user1`,
DROP FOREIGN KEY `fk_friend_user2`;

ALTER TABLE `friend`
ADD CONSTRAINT `fk_friend_user1`
FOREIGN KEY (`user1_id`) REFERENCES `user` (`user_id`)
ON DELETE CASCADE
ON UPDATE CASCADE,
ADD CONSTRAINT `fk_friend_user2`
FOREIGN KEY (`user2_id`) REFERENCES `user` (`user_id`)
ON DELETE CASCADE
ON UPDATE CASCADE;

-- -----------------------------------------------------
-- Table `wanted_game`
-- -----------------------------------------------------
ALTER TABLE `wanted_game`
DROP FOREIGN KEY `fk_wanted_game_user1`,
DROP FOREIGN KEY `fk_wanted_game_game1`;

ALTER TABLE `wanted_game`
ADD CONSTRAINT `fk_wanted_game_user1`
FOREIGN KEY (`user_id`) REFERENCES `user` (`user_id`)
ON DELETE CASCADE
ON UPDATE CASCADE,
ADD CONSTRAINT `fk_wanted_game_game1`
FOREIGN KEY (`game_id`) REFERENCES `game` (`game_id`)
ON DELETE CASCADE
ON UPDATE CASCADE;

-- -----------------------------------------------------
-- Table `game_developer`
-- -----------------------------------------------------
ALTER TABLE `game_developer`
DROP FOREIGN KEY `fk_game_developer_game1`,
DROP FOREIGN KEY `fk_game_developer_developer1`;

ALTER TABLE `game_developer`
ADD CONSTRAINT `fk_game_developer_game1`
FOREIGN KEY (`game_id`) REFERENCES `game` (`game_id`)
ON DELETE CASCADE
ON UPDATE CASCADE,
ADD CONSTRAINT `fk_game_developer_developer1`
FOREIGN KEY (`developer_id`) REFERENCES `developer` (`developer_id`)
ON DELETE CASCADE
ON UPDATE CASCADE;

-- -----------------------------------------------------
-- Table `game_category`
-- -----------------------------------------------------
ALTER TABLE `game_category`
DROP FOREIGN KEY `fk_game_category_game1`,
DROP FOREIGN KEY `fk_game_category_category1`;

ALTER TABLE `game_category`
ADD CONSTRAINT `fk_game_category_game1`
FOREIGN KEY (`game_id`) REFERENCES `game` (`game_id`)
ON DELETE CASCADE
ON UPDATE CASCADE,
ADD CONSTRAINT `fk_game_category_category1`
FOREIGN KEY (`category_id`) REFERENCES `category` (`category_id`)
ON DELETE CASCADE
ON UPDATE CASCADE;

-- -----------------------------------------------------
-- Table `owned_game`
-- -----------------------------------------------------
ALTER TABLE `owned_game`
DROP FOREIGN KEY `fk_owned_game_user1`,
DROP FOREIGN KEY `fk_owned_game_game1`;

ALTER TABLE `owned_game`
ADD CONSTRAINT `fk_owned_game_user1`
FOREIGN KEY (`user_id`) REFERENCES `user` (`user_id`)
ON DELETE CASCADE
ON UPDATE CASCADE,
ADD CONSTRAINT `fk_owned_game_game1`
FOREIGN KEY (`game_id`) REFERENCES `game` (`game_id`)
ON DELETE CASCADE
ON UPDATE CASCADE;