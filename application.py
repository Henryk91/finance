import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd
import datetime

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")

@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    cash_balance = get_user_balance()

    stocks = get_portfolio_with_price(True)
    total = total_value(cash_balance)
    msg = session["msg"]
    session["msg"] = ''
    return render_template("index.html", stocks=stocks, balance=usd(cash_balance), total=usd(total), message=msg)


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "POST":
        amount = int(request.form.get("shares"))
        if amount < 1:
            return apology('Amount should be higher than 0')
        else:
            # Make call to buy
            msg = buy_stock(request.form.get("symbol"), amount)
            if msg == 'Insufficient funds' :
                return apology('Insufficient funds')
            elif msg:
                session["msg"] = msg
                return redirect("/")
                # return render_template("index.html", message=msg)
            else:
                return apology("Unknown Symbol")

            # Then Redirect user to home page
            return redirect("/")
    else:
        # Get symbol if the query has one
        symbol = request.args.get('symbol')
        if symbol:
            return render_template("buy.html", symbol=symbol)
        else:
            return render_template("buy.html")

@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    if request.method == "POST":
        return apology("TODO")
    else:
        transactions = get_user_history()
        result=list(reversed(transactions))
        return render_template("history.html", transactions=result)

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]
        session["msg"] = ''


        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        stock_value = lookup(request.form.get("symbol"))
        if stock_value:
            msg = 'A share of ' + stock_value['name'] + ' (' + stock_value['symbol'] + ') costs $' + str(stock_value['price'])
            return render_template("quoted.html", price=msg)
        else:
            return apology("Quote error:")
        # return render_template("quote.html")
    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("Must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("Must provide password", 403)

        # Endure pass and confirm is the same
        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("Passwords don't match", 403)

        # Check if user exists
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))
        if len(rows) > 0:
            return apology("Username already exists", 403)

        # Insert new user in database
        db.execute("INSERT INTO users (username, hash) VALUES (:username,:hash)", username=request.form.get("username"), hash= generate_password_hash(request.form.get("password")))

        # Redirect user to Login
        return redirect("/login")
    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    # Gets user current stock
    stocks = get_user_portfolio()

    if request.method == "POST":
        amount = int(request.form.get("shares"))
        symbol = request.form.get('symbol')

        if amount < 1:
            return apology('Amount should be higher than 0')
        elif symbol != '-1':
            # Make call to sell
            sell_count = int(request.form.get('shares'))
            index = int(request.form.get('symbol')) - 1
            owned_count = stocks[index]['share_count']
            symbol = stocks[index]['symbol']

            # check if user can sell stock amount
            if owned_count >= sell_count:
                # Sell shares
                stock_value = lookup(symbol)
                make_trade(stock_value, amount, 'sell')
                session["msg"] = 'Sold!' # msg
            else:
                msg = "You have " + str(owned_count) + " shares of " + symbol
                return apology(msg)
            # Then Redirect user to home page
            return redirect("/")
        else:
            # User didnt select anything
            return apology("Missing Symbol")
    else:
        # Get method
        symbol = request.args.get('symbol')
        if symbol:
            # Sympol form quick sell on main page
            return render_template("sell.html", stocks=stocks, symbol=symbol)
        else:
            return render_template("sell.html", stocks=stocks)

@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    """Sell shares of stock"""
    user = get_user()
    if request.method == "POST":
        msg =  update_user(request)
        if msg == 'Profile Updated!':
            return redirect("/")
        else:
            # Error Msg
            return apology(msg)

    else:
        return render_template("profile.html", username=user['username'])


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)


# Buy stock
def buy_stock(symbol, amount):
    stock_value = lookup(request.form.get("symbol"))
    if stock_value:
        # Did get a response from lookup
        trade_msg =  make_trade(stock_value, amount, 'buy')
        if trade_msg:
            return trade_msg
        return "Bought!"
    else:
        return

# Get user data
def get_user():
    user_id = session["user_id"]
    rows = db.execute("SELECT * FROM users WHERE id = :user_id",user_id=user_id)
    if len(rows) <= 0:
            return
    else:
        return rows[0]

# Update user data
def update_user(request):
    user_id = session["user_id"]
    user_hash = generate_password_hash(request.form.get("password"))
    new_username = request.form.get("new_username")

    new_pass = request.form.get("new-password")
    new_confirm = request.form.get("new-confirm")

    user_rows = db.execute("SELECT * FROM users WHERE id = :user_id",user_id=user_id)

    # Ensure username exists and password is correct
    if len(user_rows) != 1 or not check_password_hash(user_rows[0]["hash"], request.form.get("password")):
        return apology("invalid password", 403)

    if new_pass:
        # Updating password
        if new_pass == new_confirm:
            # Update passwords
            row = db.execute("UPDATE users SET username=:new_username, hash=:new_pass WHERE id = :user_id", new_username=new_username  ,user_id=user_id, new_pass=generate_password_hash(new_pass))

            session["msg"] = 'Profile Updated!'
            return 'Profile Updated!'
        else:
            # Password Mismatch
            return "Passwords don't match"
    else:
        # Updating only username
        row = db.execute("UPDATE users SET username=:username WHERE id=:user_id", username=new_username ,user_id=user_id)
        session["msg"] = 'Profile Updated!'

        return 'Profile Updated!'

# Get user balance
def get_user_balance():
    user_id = session["user_id"]
    rows = db.execute("SELECT * FROM users WHERE id = :user_id",user_id=user_id)
    if len(rows) <= 0:
            return
    else:
        return rows[0]['cash']

# Save user balance
def set_user_balance(user_id, user_balance):
    db.execute("UPDATE users SET cash=:balance WHERE id = :user_id", balance=user_balance  ,user_id=user_id)

# Buy stock
def make_trade(stock_value, share_count, trade_type):
    balance = get_user_balance()
    price = stock_value['price']
    if balance:
        symbol = stock_value['symbol']
        user_id = session["user_id"]
        if trade_type == 'buy':

            if can_buy_check(balance, price, share_count):
                # User can buy shares
                log_trade(symbol, user_id, price, share_count, trade_type)
                post_trade_balance = balance - (price * share_count)
                set_user_balance(user_id,post_trade_balance)
                return
            else:

                # Insufficient funds
                return "Insufficient funds"
        else:
            # Selling shares
            log_trade(symbol, user_id, price, share_count, trade_type)
            post_trade_balance = balance + (price * share_count)
            set_user_balance(user_id, post_trade_balance)
    else:
        return "DB error"

# Check if user has enough funds
def can_buy_check(user_balance, price, share_count):
    if (price * share_count ) < user_balance:
        return True
    else:
        return False

# Save trade to log
def log_trade(symbol, user_id, stock_price, share_count, trade_type):

    # Insert trade in history table
    db.execute("INSERT INTO history ( symbol, user_id, stock_price, share_count, trade_type) VALUES (:symbol, :user_id, :stock_price, :share_count, :trade_type)",symbol=symbol,user_id=user_id, stock_price=stock_price,  share_count=share_count, trade_type=trade_type)

    update_user_portfolio(symbol, user_id, stock_price, share_count, trade_type)

# Get user history
def get_user_history():
    user_id = session["user_id"]
    rows = db.execute("SELECT * FROM history WHERE user_id = :user_id",user_id=user_id)
    if len(rows) <= 0:
            return [{'stock_price': '','symbol': '', 'share_count':'', 'timestamp':'', 'trade_type': ''}]
    else:
        # User has history
        return rows

# get portfolio
def get_user_portfolio():
    user_id = session["user_id"]
    rows = db.execute("SELECT * FROM portfolio WHERE user_id = :user_id AND share_count > 0;",user_id=user_id)
    if len(rows) <= 0:
            return [{'symbol': '', 'share_count': 0}]
    else:
        return rows

# get port with current prices
def get_portfolio_with_price(with_usd_format):
    stocks = get_user_portfolio()
    for stock in stocks:
        if stock['symbol'] != '':
            # Stock isnt empty
            stock_value = lookup(stock["symbol"])
            stock['name'] = stock_value['name']

            if with_usd_format:
                # Returns with values formatted for ui
                stock['price'] = usd(stock_value['price'])
                stock['total'] = usd((stock['share_count']) * stock_value['price'])
            else:
                # Returns with numerical values
                stock['price'] = stock_value['price']
                stock['total'] = (stock['share_count']) * stock_value['price']

    return stocks

# update portfolio
def update_user_portfolio(symbol, user_id, stock_price, share_count, trade_type):

    # check if stock is in portfolio
    rows = db.execute("SELECT * FROM portfolio WHERE user_id = :user_id AND symbol = :symbol",user_id=user_id, symbol=symbol)

    if rows:
        # Update portfolio
        stock_data = rows[0]
        if trade_type == 'buy':
            new_count = stock_data['share_count'] + share_count
        else:
            new_count = stock_data['share_count'] - share_count

        db.execute("UPDATE portfolio SET share_count=:share_count WHERE user_id = :user_id AND symbol=:symbol", share_count=new_count  ,user_id=user_id, symbol=symbol)
    else:
        # insert into portfolio
        db.execute("INSERT INTO portfolio (symbol, user_id, share_count) VALUES (:symbol, :user_id, :share_count)",symbol=symbol,user_id=user_id, share_count=share_count)


# Get user total asset value
def total_value(cash_balance):
    stocks = get_portfolio_with_price(False)
    ret_val = cash_balance

    for stock in stocks:
        if stock['symbol'] != '':
            # Add value of stock
            ret_val = ret_val + stock['total']

    return ret_val
