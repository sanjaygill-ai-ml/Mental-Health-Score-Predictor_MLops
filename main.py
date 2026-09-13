import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Literal
from fastapi.middleware.cors import CORSMiddleware

model = joblib.load('Mental_Health_Model.pkl')
top_countries = ['Other','India','USA','Canada','Australia','UK','Germany','Mexico','Turkey','France']

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# Catch-all: if ANYTHING crashes unexpectedly, still send back a
# proper JSON response WITH CORS headers. Without this, an
# unhandled exception skips CORSMiddleware entirely and the
# browser just reports "failed to fetch" — which is exactly the
# "Can't reach the server" message you were seeing, even though
# the server was up and actually processing the request.
@app.exception_handler(Exception)
async def handle_unexpected_error(request, exc):
    return JSONResponse(status_code=500, content={"detail": f"Internal error: {exc}"})


# A first Pydantic Model
class StudentData(BaseModel):
    age                     : int = Field(..., ge=10, le=100)
    gender                  : Literal['Male', 'Female']
    country                 : str
    academic_level          : Literal['Undergraduate', 'Graduate', 'High School']
    most_used_platform      : Literal['Facebook', 'LinkedIn', 'Instagram', 'Snapchat','Twitter','YouTube', 'TikTok', 'LINE', 'KakaoTalk', 'VKontakte', 'WhatsApp','WeChat']
    purpose_of_use          : Literal['Networking', 'Education', 'Entertainment', 'News']
    avg_daily_usage_hours   : float = Field(..., ge=0, le=24)
    daily_unlocks           : int   = Field(..., ge=0)
    study_hours             : float = Field(..., ge=0, le=24)
    physical_activity_hours : float = Field(..., ge=0, le=24)
    sleep_hours_per_night   : float = Field(..., ge=0, le=24)
    stress_level            : Literal['Medium', 'Low', 'Very High', 'High']


# Describe what we send back
class PredictionResponse(BaseModel):
    predicted_mental_health_score: float
    # 6.777777 -> float


@app.get('/')
def greet():
    return {'Welcome to Sheryians AI School Guys'}


@app.post('/predict', response_model=PredictionResponse)  # 6.77777
def predict(data: StudentData):

    country_group = data.country if data.country in top_countries else "Other"

    input_row = pd.DataFrame([{
        'Age'                       : data.age,
        'Gender'                    : data.gender,
        'Country'                   : data.country,
        'Academic_Level'            : data.academic_level,
        'Most_Used_Platform'        : data.most_used_platform,
        'Purpose_Of_Use'            : data.purpose_of_use,
        'Avg_Daily_Usage_Hours'     : data.avg_daily_usage_hours,
        'Daily_Unlocks'             : data.daily_unlocks,
        'Study_Hours'               : data.study_hours,
        'Physical_Activity_Hours'   : data.physical_activity_hours,
        'Sleep_Hours_Per_Night'     : data.sleep_hours_per_night,
        'Stress_Level'              : data.stress_level,
        'Grouped_country'           : country_group,
    }])

    try:
        prediction = model.predict(input_row)[0]  # 6.77
    except Exception as e:
        # Surface the REAL reason on the frontend (as "Prediction
        # failed: ...") instead of letting it crash unhandled.
        raise HTTPException(status_code=500, detail=f"Prediction failed: {e}")

    return PredictionResponse(predicted_mental_health_score=round(float(prediction), 2))

# uvicorn main:app --port 2200 --reload