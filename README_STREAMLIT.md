# Cricbuzz LiveStats — Streamlit App

This folder contains the upload-ready Streamlit version of the Cricbuzz LiveStats dashboard.

## Files

- `main.py` — Streamlit application with Overview, Live Matches, Player Stats, SQL Analytics, Data Manager, and Settings pages.
- `requirements.txt` — Required Python packages.

## Run locally

```bash
pip install -r requirements.txt
streamlit run main.py
```

## Deploy on Streamlit Community Cloud

1. Create or open a GitHub repository.
2. Upload `main.py`, `requirements.txt`, and this README.
3. In Streamlit Community Cloud, select the repository and branch.
4. Set the main file path to `main.py`.
5. Click **Deploy**.

The current app uses local demo data. Replace the demo data sections with your Cricbuzz API integration and SQL database connection when you are ready to connect production data.
