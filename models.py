from decimal import Decimal

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True, nullable=False)
    hash = db.Column(db.String(255), nullable=False)
    cash = db.Column(db.Numeric(15, 2), nullable=False, default=Decimal("10000.00"))

    portfolio_positions = db.relationship(
        "PortfolioPosition", back_populates="user", cascade="all, delete-orphan"
    )
    trades = db.relationship(
        "TradeHistory", back_populates="user", cascade="all, delete-orphan"
    )


class PortfolioPosition(db.Model):
    __tablename__ = "portfolio"

    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(16), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    share_count = db.Column(db.Integer, nullable=False, default=0)

    user = db.relationship("User", back_populates="portfolio_positions")

    __table_args__ = (
        db.UniqueConstraint("user_id", "symbol", name="uq_portfolio_user_symbol"),
    )


class TradeHistory(db.Model):
    __tablename__ = "history"

    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(16), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    stock_price = db.Column(db.Numeric(15, 2), nullable=False)
    share_count = db.Column(db.Integer, nullable=False)
    trade_type = db.Column(db.String(8), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, server_default=db.func.now())

    user = db.relationship("User", back_populates="trades")
