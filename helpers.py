import os
from typing import Optional

# Avoid macOS Accelerate longdouble issues triggered when numpy initializes.
os.environ.setdefault("NPY_DISABLE_LONGDOUBLE", "1")

from dotenv import load_dotenv

from flask import redirect, render_template, request, session
from functools import wraps
import yfinance as yf

load_dotenv()


def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def lookup(symbol: str) -> Optional[dict]:
    """Look up quote for symbol via yfinance."""
    if not symbol:
        return None

    symbol = symbol.strip().upper()
    # Contact API
    try:
        ticker = yf.Ticker(symbol)
        name = ticker.info.get("shortName")
        price = ticker.fast_info["last_price"]
        return {
            "name": name if name else "Not Found",
            "price": float(price) if price else float(0),
            "symbol": symbol
        }
    except Exception as e:
        print("Unexpected lookup error:", e)
        return None


def usd(value):
    """Format value as USD."""
    return f"${value:,.2f}"
