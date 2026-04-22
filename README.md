# App Store Server API — Purchase Validation Example (Python)

A minimal, self-contained Python example that shows how to **server-side validate iOS in-app purchases** using Apple's [App Store Server API](https://developer.apple.com/documentation/appstoreserverapi) and Apple's official [`app-store-server-library`](https://github.com/apple/app-store-server-library-python).

It is intentionally small so the flow (load certs → build verifier → call API → verify signed JWS → check bundle) is easy to follow.

## What it demonstrates

- Loading the Apple Root Certificates required to verify Apple-signed JWS payloads.
- Building a `SignedDataVerifier` with the correct environment (sandbox vs production) and bundle ID.
- Building an `AppStoreServerAPIClient` using a `.p8` signing key from App Store Connect.
- Fetching a single transaction via `get_transaction_info`.
- Walking paginated transaction history via `get_transaction_history` and verifying each signed transaction.
- Matching the target `transactionId` and confirming the decoded `bundleId` matches your app.

## Requirements

- Python 3.9+
- [`app-store-server-library`](https://pypi.org/project/app-store-server-library/) (Apple's official Python library)
- An [App Store Connect API key](https://developer.apple.com/documentation/appstoreserverapi/creating_api_keys_to_use_with_the_app_store_server_api) with "In-App Purchase" access (`.p8`, `KEY_ID`, `ISSUER_ID`)
- Your app's `BUNDLE_ID` and numeric `APP_APPLE_ID`
- The four Apple Root Certificates used to verify JWS signatures

## Getting the Apple Root Certificates

Download the four root CA certificates from Apple's [Certificate Authority page](https://www.apple.com/certificateauthority/) and save them under `./certs/`:

- `AppleComputerRootCertificate.cer`
- `AppleIncRootCertificate.cer`
- `AppleRootCA-G2.cer`
- `AppleRootCA-G3.cer`

## Setup

```bash
git clone https://github.com/omidsakhi/app-store-purchase-validator-python.git
cd app-store-purchase-validator-python
python -m venv .venv
# Windows: .venv\Scripts\activate
source .venv/bin/activate
pip install -r requirements.txt
```

Then open `example.py` and fill in the configuration block:

```python
KEY_ID            = "YOUR_KEY_ID"
ISSUER_ID         = "YOUR_ISSUER_ID"
BUNDLE_ID         = "com.example.yourapp"
APP_APPLE_ID      = 0000000000
ENVIRONMENT       = Environment.SANDBOX  # or Environment.PRODUCTION
PRIVATE_KEY_PATH  = "path/to/AuthKey_XXXXXXXX.p8"
```

Run it:

```bash
python example.py
```

## Notes and caveats

- **Scope:** `validate_app_store_purchase` currently filters history by `ProductType.CONSUMABLE`. If you sell subscriptions or non-consumables, adjust `productTypes` accordingly.
- **Environment matters:** Sandbox transactions will only validate against `Environment.SANDBOX`, and production against `Environment.PRODUCTION`. App Review runs in sandbox — if you handle both in one backend, use Apple's recommended fallback (try production first, then retry in sandbox on `APP_TRANSACTION_ID_NOT_SUPPORTED`-style errors).
- **Security:** Never commit your `.p8` signing key or any certificates containing private material. The included `.gitignore` excludes `*.p8`, `certs/`, and common secret files.
- **Replay protection:** In real use, record validated `transactionId`s in your own database before granting entitlement, and short-circuit re-validation on replay.

## License

Licensed under the Apache License 2.0 — see [LICENSE](LICENSE).

## Contributions

Issues and PRs are welcome. If Apple changes an API surface or a better pattern emerges in `app-store-server-library`, feel free to open a PR.
