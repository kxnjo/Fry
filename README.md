
# FryGames

FryGames is a centralized platform where users can browse and purchase games, connect with friends, and leave game reviews. It also provides price trends to help users make informed purchase decisions.

# steam? fry nicer 👩‍🍳👩‍🍳🧑‍🍳🧑‍🍳👩‍🍳👩‍🍳

# File Directory
- [Mongo Routes](./mongo_routes/)

    Find all .py files here (contains routes and noSQL queries)
  - [category.py](./mongo_routes/category.py)
  - [developer.py](./mongo_routes/developer.py)
  - [friend.py](./mongo_routes/friend.py)
  - [game.py](./mongo_routes/game.py)
  - [owned_game.py](./mongo_routes/owned_game.py)
  - [review.py](./mongo_routes/review.py)
  - [users.py](./mongo_routes/users.py)
  - [wishlist.py](./mongo_routes/wishlist.py)
  

  - [HTML Templates](./templates/)


## Start up
To create your own environment, run:
```bash
python -m venv .venv
```

Then to activate the environment:
```bash
source .venv/bin/activate
```

Install dependencies:
```bash
pip install -r requirements.txt
```

## To run the program:
```bash
python app.py
```

## For future use:
To update `requirements.txt`:
```bash
pip freeze > requirements.txt
```
