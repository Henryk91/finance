# Finance

This is a Flask/Python web app for a play money stock trading app using real stock data via api.

## Local setup

1. Create a virtual environment and install dependencies:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Copy the example environment file and update the values for your setup (Postgres connection string, Alpha Vantage key, etc):
   ```bash
   cp .env.example .env
   ```
3. Run the Flask-Migrate workflow for your database:
   ```bash
   flask db init        # only once per project
   flask db migrate -m "initial tables"
   flask db upgrade
   ```
4. Start the app with `flask run` for development or `gunicorn application:app` for production.

