from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

client = genai.Client()

app = FastAPI()


class Review(BaseModel):
    text: str


class Analysis(BaseModel):
    label: str
    score: int
    theme: str


@app.get("/")
def root():
    return {
        "message": "Customer Feedback Analyzer API is running"
    }


@app.post("/analyze")
def analyze(review: Review):

    try:

        response = client.models.generate_content(
            model="gemini-3.5-flash",
            contents=(
                "Analyze this customer review.\n"
                "label must be one of: positive, negative, neutral.\n"
                "score must be a number from 1 to 5.\n"
                "theme must be one of: service, product, delivery, other.\n"
                "theme must be one lowercase word for the main topic.\n\n"
                f"Review: {review.text}"
            ),
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=Analysis,
            ),
        )

        return response.parsed

    except Exception as e:

        error_message = str(e)

        # Print the real error in the FastAPI terminal
        print("\n========== GEMINI ERROR ==========")
        print(type(e).__name__)
        print(error_message)
        print("==================================\n")

        # Gemini quota error
        if (
            "429" in error_message
            or "RESOURCE_EXHAUSTED" in error_message
            or "quota" in error_message.lower()
        ):

            raise HTTPException(
                status_code=429,
                detail=(
                    "Gemini API quota has been exhausted. "
                    "Please wait until the quota resets or "
                    "check your Gemini API quota/billing."
                )
            )

        # Gemini temporarily unavailable
        if (
            "503" in error_message
            or "UNAVAILABLE" in error_message
        ):

            raise HTTPException(
                status_code=503,
                detail=(
                    "Gemini API is temporarily unavailable. "
                    "Please try again later."
                )
            )

        # Other Gemini errors
        raise HTTPException(
            status_code=502,
            detail=f"Gemini API error: {error_message}"
        )