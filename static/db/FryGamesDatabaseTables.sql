-- -----------------------------------------------------
-- Specify the schema to use
-- -----------------------------------------------------
USE `FryGames`;

-- -----------------------------------------------------
-- Table `user`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `user` (
  `user_id` VARCHAR(255) NOT NULL,
  `username` VARCHAR(255) NOT NULL,
  `email` VARCHAR(255) NOT NULL,
  `password` VARCHAR(255) NOT NULL,
  `created_on` DATE NOT NULL,
  PRIMARY KEY (`user_id`),
  UNIQUE INDEX `email_UNIQUE` (`email` ASC) VISIBLE)
ENGINE = InnoDB;

-- -----------------------------------------------------
-- Table `game`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `game` (
  `game_id` VARCHAR(255) NOT NULL,
  `title` VARCHAR(255) NOT NULL,
  `release_date` VARCHAR(255) NOT NULL,
  `price` FLOAT NOT NULL,
  PRIMARY KEY (`game_id`))
ENGINE = InnoDB;

-- -----------------------------------------------------
-- Table `category`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `category` (
  `category_id` VARCHAR(255) NOT NULL,
  `category_name` VARCHAR(45) NOT NULL,
  PRIMARY KEY (`category_id`))
ENGINE = InnoDB;

-- -----------------------------------------------------
-- Table `review`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `review` (
  `review_id` VARCHAR(255) NOT NULL,
  `review_text` VARCHAR(1000) NULL,
  `review_date` DATE NULL,
  `user_id` VARCHAR(255) NOT NULL,
  `game_id` VARCHAR(255) NOT NULL,
  PRIMARY KEY (`review_id`, `game_id`),
  INDEX `fk_review_game1_idx` (`game_id` ASC) VISIBLE,
  INDEX `fk_review_user1_idx` (`user_id` ASC) VISIBLE,
  CONSTRAINT `fk_review_game1`
    FOREIGN KEY (`game_id`)
    REFERENCES `game` (`game_id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `fk_review_user1`
    FOREIGN KEY (`user_id`)
    REFERENCES `user` (`user_id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE)
ENGINE = InnoDB;

-- -----------------------------------------------------
-- Table `developer`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `developer` (
  `developer_id` VARCHAR(255) NOT NULL,
  `developer_name` VARCHAR(255) NOT NULL,
  PRIMARY KEY (`developer_id`))
ENGINE = InnoDB;

-- -----------------------------------------------------
-- Table `price_change`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `price_change` (
  `price_id` VARCHAR(255) NOT NULL,
  `game_id` VARCHAR(255) NOT NULL,
  `change_date` VARCHAR(255) NOT NULL,
  `base_price` FLOAT NOT NULL,
  `discount` INT NOT NULL,
  PRIMARY KEY (`price_id`, `game_id`),
  INDEX `fk_price_change_game1_idx` (`game_id` ASC) VISIBLE,
  CONSTRAINT `fk_price_change_game1`
    FOREIGN KEY (`game_id`)
    REFERENCES `game` (`game_id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE)
ENGINE = InnoDB;

-- -----------------------------------------------------
-- Table `friend`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `friend` (
  `user1_id` VARCHAR(255) NOT NULL, -- The ID of the first user
  `user2_id` VARCHAR(255) NOT NULL, -- The ID of the second user (friend)
  `friendship_date` DATE NULL,
  PRIMARY KEY (`user1_id`, `user2_id`),
  INDEX `fk_friend_user1_idx` (`user1_id` ASC) VISIBLE,
  INDEX `fk_friend_user2_idx` (`user2_id` ASC) VISIBLE,
  CONSTRAINT `fk_friend_user1`
    FOREIGN KEY (`user1_id`)
    REFERENCES `user` (`user_id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `fk_friend_user2`
    FOREIGN KEY (`user2_id`)
    REFERENCES `user` (`user_id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE)
ENGINE = InnoDB;

-- -----------------------------------------------------
-- Table `wanted_game`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `wanted_game` (
  `user_id` VARCHAR(255) NOT NULL,
  `game_id` VARCHAR(255) NOT NULL,
  `added_date` DATE NOT NULL,
  PRIMARY KEY (`user_id`, `game_id`),
  INDEX `fk_wanted_game_user1_idx` (`user_id` ASC) VISIBLE,
  INDEX `fk_wanted_game_game1_idx` (`game_id` ASC) VISIBLE,
  CONSTRAINT `fk_wanted_game_user1`
    FOREIGN KEY (`user_id`)
    REFERENCES `user` (`user_id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `fk_wanted_game_game1`
    FOREIGN KEY (`game_id`)
    REFERENCES `game` (`game_id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE)
ENGINE = InnoDB;


-- -----------------------------------------------------
-- Table `game_has_developer`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `game_developer` (
  `game_id` VARCHAR(255) NOT NULL,
  `developer_id` VARCHAR(255) NOT NULL,
  PRIMARY KEY (`game_id`, `developer_id`),
  INDEX `fk_game_developer_developer1_idx` (`developer_id` ASC) VISIBLE,
  INDEX `fk_game_developer_game1_idx` (`game_id` ASC) VISIBLE,
  CONSTRAINT `fk_game_developer_game1`
    FOREIGN KEY (`game_id`)
    REFERENCES `game` (`game_id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `fk_game_developer_developer1`
    FOREIGN KEY (`developer_id`)
    REFERENCES `developer` (`developer_id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE)
ENGINE = InnoDB;

-- -----------------------------------------------------
-- Table `game_has_category`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `game_category` (
  `game_id` VARCHAR(255) NOT NULL,
  `category_id` VARCHAR(255) NOT NULL,
  PRIMARY KEY (`game_id`, `category_id`),
  INDEX `fk_game_category_category1_idx` (`category_id` ASC) VISIBLE,
  INDEX `fk_game_category_game1_idx` (`game_id` ASC) VISIBLE,
  CONSTRAINT `fk_game_category_game1`
    FOREIGN KEY (`game_id`)
    REFERENCES `game` (`game_id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `fk_game_category_category1`
    FOREIGN KEY (`category_id`)
    REFERENCES `category` (`category_id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE)
ENGINE = InnoDB;

-- -----------------------------------------------------
-- Table `user_has_game`
-- -----------------------------------------------------
CREATE TABLE IF NOT EXISTS `owned_game` (
  `user_id` VARCHAR(255) NOT NULL,
  `game_id` VARCHAR(255) NOT NULL,
  `purchase_date` DATE NOT NULL,
  `hours_played` FLOAT NOT NULL,
  PRIMARY KEY (`user_id`, `game_id`),
  INDEX `fk_owned_game_game1_idx` (`game_id` ASC) VISIBLE,
  INDEX `fk_owned_game_user1_idx` (`user_id` ASC) VISIBLE,
  CONSTRAINT `fk_owned_game_user1`
    FOREIGN KEY (`user_id`)
    REFERENCES `user` (`user_id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE,
  CONSTRAINT `fk_owned_game_game1`
    FOREIGN KEY (`game_id`)
    REFERENCES `game` (`game_id`)
    ON DELETE CASCADE
    ON UPDATE CASCADE)
ENGINE = InnoDB;
