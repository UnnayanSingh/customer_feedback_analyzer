# Customer Feedback Analyzer

A web app that turns customer reviews into sentiment labels, scores, and topic insights. It uses Streamlit for the interface, FastAPI for the analysis endpoint, Google Gemini for analysis, and SQLite for saved results.

## Try the live app

- **App:** [customer-feedback-insights.streamlit.app](https://customer-feedback-insights.streamlit.app/)
- **API status:** [customer-feedback-analyzer-4ap3.onrender.com](https://customer-feedback-analyzer-4ap3.onrender.com/)

The API may take a little time to respond after being idle. The live demo also shares one Gemini API quota across visitors, so analysis can be temporarily unavailable if that quota is reached.

## What it does

- Analyze multiple reviews, with one review on each line.
- Classify each review as positive, neutral, or negative.
- Give each review a score from 1 to 5 and a topic: service, product, delivery, or other.
- Show summary metrics, sentiment counts, and charts for sentiment and topics.
- Save analyzed reviews and view history from the current app session.
- Switch between light and dark themes from **⋮ → Settings → Theme**.

Download the displayed results or history table as a CSV from its table toolbar. Importing a CSV to restore history is not currently supported.

## Screenshots

These sample screenshots show the app in dark mode. The live app also supports light mode.

### Review input

![Customer review input and analysis status](screenshots/review-input.png)

### Insights dashboard

![Sentiment and topic insights dashboard](screenshots/insights-dashboard.png)

### Detailed results

![Detailed review analysis results](screenshots/detailed-results.png)

### Saved history

![Saved customer feedback history](screenshots/saved-history.png)

## Run it locally

### Requirements

- Python 3.10 or newer
- A [Google Gemini API key](https://aistudio.google.com/apikey)
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

### 1. Get the project

```bash
git clone https://github.com/UnnayanSingh/customer_feedback_analyzer.git
cd customer_feedback_analyzer
```

### 2. Add your Gemini API key

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_gemini_api_key
```

Keep this key private. `.env` is excluded from Git by `.gitignore`.

### 3. Install dependencies

With uv:

```bash
uv sync
```

Or with pip:

```bash
python -m pip install -r requirements.txt
```

### 4. Start the API and app

Open two terminals in the project folder.

In the first terminal, start the FastAPI backend:

```bash
uv run uvicorn api:app --reload
```

In the second terminal, start Streamlit:

```bash
uv run streamlit run app.py
```

Open the local URL printed by Streamlit, usually <http://localhost:8501>. The API runs at <http://127.0.0.1:8000>.

If you installed with pip, run `uvicorn api:app --reload` and `streamlit run app.py` without `uv run`.

The frontend uses `http://127.0.0.1:8000/analyze` by default. To point it at a different API, add an optional `API_URL` value to `.env`:

```env
API_URL=https://your-api.example.com/analyze
```

## Deploy your own copy

The project runs as two services: a FastAPI backend and a Streamlit frontend.

### FastAPI backend on Render

1. Create a Render **Web Service** connected to this repository and the `master` branch.
2. Set the build command to `pip install -r requirements.txt`.
3. Set the start command to `uvicorn api:app --host 0.0.0.0 --port $PORT`.
4. Add `GEMINI_API_KEY` as an environment variable in Render. Do not commit the key to GitHub.
5. Deploy, then copy the service URL.

### Streamlit frontend on Community Cloud

1. Create an app from this repository, select the `master` branch, and set the main file to `app.py`.
2. Open the app's **Settings → Secrets** and add the URL of your Render API:

```toml
API_URL = "https://your-api.onrender.com/analyze"
```

The `.streamlit/config.toml` file defines the app's light and dark themes. The visitor can choose either from the Streamlit settings menu.

## Saved history and demo limits

Saved reviews are stored in a local SQLite file named `feedback.db` and filtered to the current Streamlit session. Other visitors do not see that session's history. There is no sign-in or account-based history, and local database files on hosted services are not guaranteed to survive restarts or redeploys.

All visitors to a deployment share the Gemini API quota configured for its backend. The app sends one Gemini request per review, so high usage may cause the service to temporarily reach its limit. Check the quota in [Google AI Studio](https://aistudio.google.com/).

## API

The backend provides a status endpoint and an analysis endpoint:

- `GET /` — reports that the API is running.
- `POST /analyze` — analyzes one review.

Example request:

```http
POST /analyze
Content-Type: application/json

{"text": "The staff were friendly and the food was excellent."}
```

Example response:

```json
{
  "label": "positive",
  "score": 5,
  "theme": "service"
}
```

## Project structure

```text
.
├── .streamlit/
│   └── config.toml       # Light and dark theme settings
├── screenshots/          # Images used in this README
├── api.py                # FastAPI endpoint and Gemini integration
├── app.py                # Streamlit user interface
├── database.py           # SQLite save and history functions
├── sample_reviews.txt    # Example reviews
├── requirements.txt      # Dependencies for pip and deployment
├── pyproject.toml        # Project metadata and dependencies
└── uv.lock               # Locked dependency versions for uv
```
