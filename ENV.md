ETORO_API_KEY and ETORO_USER_KEY
https://www.etoro.com/settings/trade

(Market quotes use Yahoo Finance via the `yfinance` library — no API key required.)

SECRET_KEY
python -c "import secrets; print(secrets.token_hex(32))"

DATABASE_URL, POSTGRES_USER, POSTGRES_PASSWORD, and POSTGRES_DB
As in docker container

Banca Transilvania Open Banking (PSD2 Sandbox)
BT uses an automated Dynamic Client Registration process for the Sandbox.
You can dynamically register your app by sending a POST request to:
`https://api.apistorebt.ro/bt/sb/oauth/register`
Example payload: `{"redirect_uris": ["http://localhost:8000/api/v1/bank/oauth2/callback"], "client_name": "My App"}`
This will return a new `client_id` and `client_secret` to put in `.env`.
