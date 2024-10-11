from flask import Blueprint, render_template, request, session
import mysql.connector
import config

# Create a Blueprint object
game_bp = Blueprint("game_bp", __name__)


def create_connection():
    # Replace with your database connection details
    return mysql.connector.connect(
        host=config.HOST,
        user=config.USER,
        password=config.PASSWORD,
        database=config.DATABASE,
    )


@game_bp.route("/games", methods=['GET'])
def view_all_games():
    search = request.args.get('query')
    page = request.args.get('page', 1, type=int)
    sort_by = request.args.get('sort', 'title')  # Default sort is by title
    sort_order = request.args.get('order', 'asc')  # Default order is ascending

    # Define the limit of items per page
    per_page = 10

    # Calculate the offset for the SQL query
    offset = (page - 1) * per_page

    if sort_by == 'price':
        order_by = 'g.price'
    elif sort_by == 'release_date':
        order_by = 'g.release_date'
    else:
        order_by = 'g.title'  # Default is alphabetically by title

    order_direction = 'ASC' if sort_order == 'asc' else 'DESC'

    conn = create_connection()
    cur = conn.cursor()

    if search:
        query = f'''
        SELECT 
            g.game_id,
            g.title,
            g.release_date,
            g.price
        FROM 
            game g
        WHERE
            g.title 
        LIKE 
            %s
        ORDER BY 
            {order_by} {order_direction}
        LIMIT %s OFFSET %s
        '''
        search_term = f"{search}%"
        cur.execute(query, (search_term, per_page, offset))
        rows = cur.fetchall()

        # Get total number of results for pagination
        count_query = '''
        SELECT COUNT(*) FROM game g WHERE g.title LIKE %s
        '''
        cur.execute(count_query, (search_term,))
        total = cur.fetchone()[0]

    else:
        query = f'''
        SELECT 
            g.game_id,
            g.title,
            g.release_date,
            g.price
        FROM 
            game g
        ORDER BY 
            {order_by} {order_direction}
        LIMIT %s OFFSET %s
        '''

        # Execute the query with the limit and offset parameters
        cur.execute(query, (per_page, offset))
        rows = cur.fetchall()

        # Get total number of results for pagination
        count_query = '''
        SELECT COUNT(*) FROM game g
        '''
        cur.execute(count_query)
        total = cur.fetchone()[0]

    # Create a list to hold game data
    games = []
    if rows:
        for row in rows:
            game_data = {
                "game_id": row[0],
                "game_title": row[1],
                "game_release_date": row[2],
                "game_price": row[3]
            }
            games.append(game_data)
    else:
        print("not found")

    return render_template("games/view_games.html", games=games, page=page, sort_by=sort_by,
                           sort_order=sort_order, search=search)

@game_bp.route("/game/<game_id>")
def view_game(game_id):
    conn = create_connection()
    cur = conn.cursor(buffered=True)

    # Fetch game details
    cur.execute('''
        SELECT
            g.game_id,
            g.title,
            g.release_date,
            g.price
        FROM
            game g
        WHERE
            g.game_id = %s
        LIMIT 1;
    ''', (game_id,))
    game = cur.fetchone()

    if not game:
        return "Game not found", 404

    game_data = {
        "game_id": game[0],
        "game_title": game[1],
        "game_release_date": game[2],
        "game_price": game[3]
    }

    cur.execute('''
    SELECT 
        c.category_id, c.category_name
    FROM 
        category c
    JOIN 
        game_category gc 
    ON 
        c.category_id = gc.category_id
    WHERE 
        gc.game_id = %s
    ;
    ''', (game_id,))
    rows = cur.fetchall()

    categories = []
    if rows:
        for row in rows:
            category = {
                "category_id": row[0],
                "category_name": row[1],
            }
            categories.append(category)
    else:
        print("not found")

    cur.execute('''
    SELECT 
        d.developer_id, d.developer_name
    FROM 
        developer d
    JOIN 
        game_developer gd 
    ON 
        d.developer_id = gd.developer_id
    WHERE 
        gd.game_id = %s
    ;
    ''', (game_id,))
    rows = cur.fetchall()

    developers = []
    if rows:
        for row in rows:
            developer = {
                "developer_id": row[0],
                "developer_name": row[1],
            }
            developers.append(developer)
    else:
        print("not found")


    # Retrieve Reviews from DB
    cur.execute('''
        SELECT
            r.review_id, r.review_text, r.review_date, u.username, g.title, r.recommended
        FROM
            review r
        JOIN user u ON r.user_id = u.user_id
        JOIN game g ON r.game_id = g.game_id
        WHERE
            g.game_id = %s
        ORDER BY
            r.review_date DESC
        LIMIT 10
    ''', (game_id,))
    reviews = []

    # Fetch the review rows
    review_rows = cur.fetchall()
    if review_rows:
        for row in review_rows:
            if row[5] == 'TRUE':
                recommended_val = "RECOMMENDED"
            else:
                recommended_val = "NOT RECOMMENDED"

            review_data = {
                "review_id": row[0],
                "review_text": row[1],
                "review_date": row[2],
                "user_id": row[3],
                "game_id": row[4],
                "recommended": recommended_val
            }
            reviews.append(review_data)

    # Count recommended / non-recommended reviews
    cur.execute('''
        SELECT
            SUM(review.recommended = 'TRUE') AS true_count,
            SUM(review.recommended = 'FALSE') AS false_count
        FROM
            review
        WHERE
            review.game_id = %s;
    ''', (game_id,))
    recommended_data = dict(zip(["true_count", "false_count"], cur.fetchone() or (0, 0)))

    # Check if the user is logged in
    user_id = session.get('user_id')
    gameInWishlist = False
    get_user_review = None
    user_owned = False  # Initialize user_owned to False

    if user_id:
        # Check if the game is in the user's wishlist
        cur.execute('''
            SELECT 1 FROM wanted_game
            WHERE user_id = %s AND game_id = %s;
        ''', (user_id, game_id))

        gameInWishlist = cur.fetchone() is not None  # Correctly check wishlist

        # Fetch user review
        cur.execute('''
            SELECT r.review_id, g.title, r.review_date, r.review_text, r.recommended
            FROM review r
            JOIN game g ON g.game_id = r.game_id
            WHERE r.game_id = %s AND r.user_id = %s
        ''', (game_id, user_id))

        get_user_review = cur.fetchone()  # Get the review or None

        # Check if the user owns the game
        cur.execute('''
            SELECT EXISTS (
                SELECT 1
                FROM owned_game
                WHERE user_id = %s AND game_id = %s
            )
        ''', (user_id, game_id))

        result = cur.fetchone()
        user_owned = result[0] if result is not None else False  # Check ownership

    # get price history data 
    cur.execute('''
        SELECT 
            price_id, 
            change_date, 
            base_price, 
            discount 
        FROM 
            price_change
        WHERE 
            game_id = %s
        ORDER BY 
            change_date ASC
    ''', (game_id,))
    price_changes = cur.fetchall()
    print(price_changes)

    # Prepare data for the graph
    dates = []
    prices = []

    for change in price_changes:
        # Extract and format change_date to 'dd-mm-yyyy'
        formatted_date = change[1].strftime('%d-%m-%Y')
        dates.append(formatted_date)  # Append formatted date
        final_price = change[2] - (change[2] * (change[3] / 100))  # Apply discount to base_price
        prices.append(final_price)


    return render_template("games/game.html",
                           game=game_data,
                           categories=categories,
                           developers=developers,
                           reviews=reviews,
                           recommended_data=recommended_data,
                           gameInWishlist=gameInWishlist,
                           user_logged_in=bool(user_id),
                           user_owned=bool(user_owned),
                           get_user_review=get_user_review,
                           dates=dates,
                           prices=prices)
