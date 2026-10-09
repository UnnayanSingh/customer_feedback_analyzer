"""Customer Feedback Analyzer Streamlit frontend.

Run the API and frontend in separate terminals:

    uv run uvicorn api:app --reload
    uv run streamlit run app.py
"""

from collections import Counter

import requests
import streamlit as st

from database import DB_FILE, init_db, load_history, save_results


API_URL = "http://127.0.0.1:8000/analyze"
VALID_LABELS = {"positive", "neutral", "negative"}
VALID_THEMES = {"service", "product", "delivery", "other"}


st.set_page_config(
    page_title="Customer Feedback Analyzer",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .stApp { background: #0e1117; }
    .block-container { max-width: 1400px; padding-top: 2rem; padding-bottom: 3rem; }
    [data-testid="stMetric"] {
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 12px;
        padding: 16px;
    }
    .stButton > button { border-radius: 9px; font-weight: 600; }
    </style>
    """,
    unsafe_allow_html=True,
)

init_db()

if "results" not in st.session_state:
    st.session_state.results = []
if "results_saved" not in st.session_state:
    st.session_state.results_saved = False
if "analysis_message" not in st.session_state:
    st.session_state.analysis_message = None
if "analysis_message_type" not in st.session_state:
    st.session_state.analysis_message_type = "info"


def validate_analysis(data):
    """Return a normalized analysis result or raise ValueError."""
    if not isinstance(data, dict):
        raise ValueError("The backend returned an invalid response format.")

    label = data.get("label")
    score = data.get("score")
    theme = data.get("theme")

    if not isinstance(label, str) or label.lower() not in VALID_LABELS:
        raise ValueError("The backend returned an unsupported sentiment label.")
    if isinstance(score, bool) or not isinstance(score, int) or not 1 <= score <= 5:
        raise ValueError("The backend returned a score outside the 1–5 range.")
    if not isinstance(theme, str) or theme.lower() not in VALID_THEMES:
        raise ValueError("The backend returned an unsupported topic.")

    return {
        "label": label.lower(),
        "score": score,
        "theme": theme.lower(),
    }


with st.sidebar:
    st.header("⚙️ Dashboard")
    st.write("Analyze customer feedback with the FastAPI backend and Gemini.")
    st.divider()
    st.subheader("Backend")
    st.code(API_URL, language="text")
    st.caption("Start FastAPI and Streamlit in separate terminals.")
    st.divider()

    if st.button("🧹 Clear current results", use_container_width=True):
        st.session_state.results = []
        st.session_state.results_saved = False
        st.session_state.analysis_message = None
        st.rerun()

    st.divider()
    st.caption("FastAPI · Gemini · Streamlit · SQLite")


st.title("📝 Customer Feedback Analyzer")
st.write("Turn customer reviews into sentiment, score, and topic insights.")

st.subheader("📥 Customer reviews")
st.caption("Enter one review per line.")

reviews_text = st.text_area(
    "Reviews",
    height=220,
    placeholder=(
        "The food was excellent and the staff were friendly.\n"
        "The delivery was late and the food was cold.\n"
        "Great quality but the portions were small."
    ),
    label_visibility="collapsed",
)

if st.button("🚀 Analyze reviews", type="primary", use_container_width=True):
    reviews = [line.strip() for line in reviews_text.splitlines() if line.strip()]
    st.session_state.results = []
    st.session_state.results_saved = False
    st.session_state.analysis_message = None

    if not reviews:
        st.warning("Please enter at least one customer review.")
    else:
        results = []
        failure_message = None
        failure_type = "error"
        progress = st.progress(0, text="Starting analysis…")
        status = st.empty()

        for index, review in enumerate(reviews):
            status.info(f"🔍 Analyzing review {index + 1} of {len(reviews)}…")

            try:
                response = requests.post(
                    API_URL,
                    json={"text": review},
                    timeout=30,
                )

                if response.status_code == 429:
                    try:
                        detail = response.json().get("detail", "")
                    except (ValueError, AttributeError):
                        detail = ""
                    failure_message = str(detail) or "Gemini API quota has been exhausted."
                    failure_type = "warning"
                    break

                if response.status_code >= 400:
                    try:
                        detail = response.json().get("detail", "")
                    except (ValueError, AttributeError):
                        detail = ""

                    if response.status_code in (502, 503):
                        failure_message = (
                            str(detail)
                            or "The AI service is unavailable. Please try again later."
                        )
                    else:
                        failure_message = (
                            str(detail)
                            or f"The backend returned HTTP {response.status_code}."
                        )
                    break

                try:
                    data = response.json()
                except ValueError as error:
                    raise ValueError("The backend returned invalid JSON.") from error

                analysis = validate_analysis(data)
                results.append({"review": review, **analysis})

                progress.progress(
                    (index + 1) / len(reviews),
                    text=f"Analyzed {index + 1} of {len(reviews)} reviews",
                )

            except requests.exceptions.ConnectionError:
                failure_message = (
                    "Cannot connect to FastAPI. Start the backend with "
                    "`uv run uvicorn api:app --reload`."
                )
                break
            except requests.exceptions.Timeout:
                failure_message = "The AI service took too long to respond. Please try again."
                break
            except ValueError as error:
                failure_message = str(error)
                break
            except requests.exceptions.RequestException as error:
                failure_message = f"Could not contact the backend: {error}"
                break

        progress.empty()
        status.empty()
        st.session_state.results = results

        if failure_message:
            st.session_state.analysis_message = failure_message
            st.session_state.analysis_message_type = failure_type
        elif results:
            st.session_state.analysis_message = (
                f"Successfully analyzed {len(results)} review(s)."
            )
            st.session_state.analysis_message_type = "success"

if st.session_state.analysis_message:
    message_type = st.session_state.analysis_message_type
    if message_type == "warning":
        st.warning(st.session_state.analysis_message)
    elif message_type == "success":
        st.success(st.session_state.analysis_message)
    else:
        st.error(st.session_state.analysis_message)


results = st.session_state.results

if results:
    st.divider()
    st.header("📊 Analysis overview")

    positive_count = sum(result["label"] == "positive" for result in results)
    neutral_count = sum(result["label"] == "neutral" for result in results)
    negative_count = sum(result["label"] == "negative" for result in results)
    average_score = round(sum(result["score"] for result in results) / len(results), 1)
    top_theme = Counter(result["theme"] for result in results).most_common(1)[0][0]

    metric_columns = st.columns(4)
    metric_columns[0].metric("Reviews analyzed", len(results))
    metric_columns[1].metric("Average score", f"{average_score}/5")
    metric_columns[2].metric(
        "Positive reviews",
        f"{positive_count} ({round(positive_count / len(results) * 100)}%)",
    )
    metric_columns[3].metric("Top topic", top_theme.title())

    st.subheader("😊 Sentiment breakdown")
    sentiment_columns = st.columns(3)
    sentiment_columns[0].metric("😊 Positive", positive_count)
    sentiment_columns[1].metric("😐 Neutral", neutral_count)
    sentiment_columns[2].metric("😞 Negative", negative_count)

    st.subheader("📈 Insights")
    chart_columns = st.columns(2)
    with chart_columns[0]:
        st.write("**Sentiment distribution**")
        sentiment_data = [
            {"Sentiment": "Positive", "Count": positive_count, "Color": "#22c55e"},
            {"Sentiment": "Neutral", "Count": neutral_count, "Color": "#f59e0b"},
            {"Sentiment": "Negative", "Count": negative_count, "Color": "#ef4444"},
        ]
        st.bar_chart(
            sentiment_data,
            x="Sentiment",
            y="Count",
            color="Color",
            sort=False,
        )
    with chart_columns[1]:
        st.write("**Review topics**")
        topic_palette = {
            "service": "#38bdf8",
            "product": "#a78bfa",
            "delivery": "#fb923c",
            "other": "#f472b6",
        }
        topic_counts = Counter(result["theme"] for result in results)
        topic_data = [
            {
                "Topic": topic.title(),
                "Count": count,
                "Color": topic_palette[topic],
            }
            for topic, count in topic_counts.items()
        ]
        st.bar_chart(
            topic_data,
            x="Topic",
            y="Count",
            color="Color",
            sort=False,
        )

    st.subheader("📋 Detailed results")
    numbered_results = [
        {"No.": index, **result}
        for index, result in enumerate(results, start=1)
    ]
    st.dataframe(numbered_results, use_container_width=True, hide_index=True)

    st.subheader("💾 Save report")
    if st.button(
        "Saved to database" if st.session_state.results_saved else "Save results to database",
        use_container_width=True,
        disabled=st.session_state.results_saved,
    ):
        try:
            save_results(results)
            st.session_state.results_saved = True
            st.success("Feedback saved successfully.")
        except Exception as error:
            st.error(f"Could not save results: {error}")


st.divider()
st.subheader("📚 Saved history")

with st.expander("View previously saved reviews"):
    try:
        history = load_history()
        if history:
            st.caption(f"{len(history)} review(s) saved in the database.")
            history_data = [
                {
                    "No.": index,
                    "Review": row[0],
                    "Sentiment": row[1],
                    "Score": row[2],
                    "Topic": row[3],
                }
                for index, row in enumerate(history, start=1)
            ]
            st.dataframe(history_data, use_container_width=True, hide_index=True)
        else:
            st.info("No saved reviews yet.")
    except Exception as error:
        st.error(f"Could not load saved history: {error}")

st.caption("Customer Feedback Analyzer · FastAPI · Gemini · Streamlit · SQLite")
