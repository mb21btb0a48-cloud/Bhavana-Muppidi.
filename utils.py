# Import streamlit for caching
import streamlit as st
# Import requests for API calls
import requests
# Import base64 for image encoding
import base64
# Import PyPDF2 for PDF parsing
import PyPDF2
# Import Document for DOCX parsing
from docx import Document

# Fetch and return a Lottie animation JSON from a URL
@st.cache_data(show_spinner=False)
def load_lottieurl(url: str):
    try:
        # Make a GET request to the URL
        r = requests.get(url)
        # Return the JSON if the request was successful
        return r.json() if r.status_code == 200 else None
    except:
        # Return None if any error occurs
        return None

# Extract text content from an uploaded PDF file
def extract_pdf_text(file):
    try:
        # Initialize a PDF reader object
        reader = PyPDF2.PdfReader(file)
        # Extract and join text from all pages
        return "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])
    except Exception as e:
        # Return an error message if extraction fails
        return f"Error extracting PDF: {e}"

# Extract text content from an uploaded DOCX file
def extract_docx_text(file):
    try:
        # Initialize a DOCX document object
        doc = Document(file)
        # Extract and join text from all paragraphs
        return "\n".join([para.text for para in doc.paragraphs])
    except Exception as e:
        # Return an error message if extraction fails
        return f"Error extracting DOCX: {e}"

# Convert an uploaded image file to a base64 encoded string
def get_image_base64(file):
    # Read the file bytes and encode to base64, then decode to string
    return base64.b64encode(file.getvalue()).decode("utf-8")

# Transcribe spoken audio to text using OpenAI Whisper
def transcribe_audio(client, audio_bytes):
    import io
    try:
        # Whisper requires a "file-like" object with a .name attribute matching known audio extensions
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = "recording.wav"
        # Create a transcription request
        transcription = client.audio.transcriptions.create(
            model="whisper-1", 
            file=audio_file
        )
        return transcription.text
    except Exception as e:
        return f"Error transcribing audio: {e}"

# Generate Text-to-Speech audio bytes from text using OpenAI TTS
def generate_audio_summary(client, text_summary):
    try:
        # Create a highly realistic TTS speech generation
        response = client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=text_summary
        )
        return response.content
    except Exception as e:
        return None

import math

def calculate_distance(lat1, lon1, lat2, lon2):
    try:
        R = 6371.0 # Earth radius in kilometers
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return round(R * c, 1)
    except Exception:
        return 999.9

def get_location_name(lat, lng):
    if not lat or not lng:
        return None
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lng}&format=json"
        headers = {"User-Agent": "AIHealthDashboard/1.0"}
        response = requests.get(url, headers=headers, timeout=5)
        if response.status_code == 200:
            data = response.json()
            address = data.get("address", {})
            state = address.get("state", "")
            country = address.get("country", "")
            if state and country:
                return f"{state}, {country}"
            elif country:
                return country
            else:
                return data.get("display_name", "")
    except Exception as e:
        print(f"Geocoding error: {e}")
    return None

# ADVANCED: Web Crawler API for real-time restaurant and menu discovery
def fetch_local_health_restaurants(disease, lat, lng, city_name, api_key):
    try:
        # If no API key is provided, return premium mocked nearby restaurants for UI testing
        if not api_key:
            return [
                {"name": "Green Bowl Superfoods", "rating": 4.8, "address": f"{city_name if city_name else 'Local City Center'}", "distance_km": 2.4, "snippet": f"Healthy, organic bowls perfect for {disease}."},
                {"name": "FitBites Kitchen", "rating": 4.6, "address": "Downtown Healthy District", "distance_km": 5.1, "snippet": f"Dietitian-approved {disease} friendly meals."},
                {"name": "The Protein Spot", "rating": 4.5, "address": "Nearby Fitness Plaza", "distance_km": 8.7, "snippet": "High protein dishes, strictly within your 10km GPS radius."}
            ]
            
        url = "https://serpapi.com/search.json"
        
        # We inject the exact coordinates into the search query string itself.
        # This acts as an unshakeable anchor for Google's algorithm, forcing it to
        # search *exactly* here regardless of backend server IP proxy locations.
        if city_name:
            query_string = f"Healthy {disease} restaurants near {city_name}"
        elif lat and lng:
            query_string = f"Healthy {disease} restaurants near {lat},{lng}"
        else:
            query_string = f"Healthy {disease} restaurants"

        params = {
            "engine": "google_local",
            "q": query_string,
            "hl": "en", # Strict English context
            "type": "search",
            "api_key": api_key
        }
        
        # Strictly use exact GPS coordinates instead of sweeping city search to guarantee nearby proximity
        if lat and lng:
            params["ll"] = f"@{lat},{lng},15z"
            
        r = requests.get(url, params=params)
        if r.status_code == 200:
            data = r.json()
            local_results = data.get("local_results", [])
            
            structured_results = []
            for res in local_results:
                # Calculate exact distance from user's GPS
                dist = 999.9
                coords = res.get("gps_coordinates")
                if coords and lat and lng:
                    dist = calculate_distance(float(lat), float(lng), float(coords.get("latitude")), float(coords.get("longitude")))
                
                # If searching by city_name without lat/lng, bypass exact distance bounds
                if dist <= 10.0 or (city_name and not (lat and lng)):
                    structured_results.append({
                        "name": res.get("title"),
                        "rating": res.get("rating"),
                        "address": res.get("address"),
                        "distance_km": dist if (lat and lng) else None,
                        "snippet": res.get("description", "Top healthy diet choice")
                    })
            
            # Sort all fetched results explicitly by closest distance first
            if lat and lng:
                structured_results.sort(key=lambda x: x["distance_km"])
            
            # Return only the top 5 closest restaurants
            return structured_results[:5]
            
        return []
    except Exception as e:
        return []

# --- VERHOEFF ALGORITHM (For Aadhar Validation) ---
VERHOEFF_TABLE_D = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    [1, 2, 3, 4, 0, 6, 7, 8, 9, 5],
    [2, 3, 4, 0, 1, 7, 8, 9, 5, 6],
    [3, 4, 0, 1, 2, 8, 9, 5, 6, 7],
    [4, 0, 1, 2, 3, 9, 5, 6, 7, 8],
    [5, 9, 8, 7, 6, 0, 4, 3, 2, 1],
    [6, 5, 9, 8, 7, 1, 0, 4, 3, 2],
    [7, 6, 5, 9, 8, 2, 1, 0, 4, 3],
    [8, 7, 6, 5, 9, 3, 2, 1, 0, 4],
    [9, 8, 7, 6, 5, 4, 3, 2, 1, 0]
]
VERHOEFF_TABLE_P = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    [1, 5, 7, 6, 2, 8, 3, 0, 9, 4],
    [5, 8, 0, 3, 7, 9, 6, 1, 4, 2],
    [8, 9, 1, 6, 0, 4, 3, 5, 2, 7],
    [9, 4, 5, 3, 1, 2, 6, 8, 7, 0],
    [4, 2, 8, 6, 5, 7, 3, 9, 0, 1],
    [2, 7, 9, 3, 8, 0, 6, 4, 1, 5],
    [7, 0, 4, 6, 9, 1, 3, 2, 5, 8]
]
VERHOEFF_TABLE_INV = [0, 4, 3, 2, 1, 5, 6, 7, 8, 9]

def validate_aadhar(number: str) -> bool:
    """Validate 12-digit Aadhar using Verhoeff algorithm."""
    if not number or not number.isdigit() or len(number) != 12:
        return False
    
    # Structural check (UIDAI requirement: Doesn't start with 0 or 1)
    if number[0] in ['0', '1']:
        return False

    # Verhoeff Checksum Logic
    c = 0
    for i, digit in enumerate(reversed(number)):
        c = VERHOEFF_TABLE_D[c][VERHOEFF_TABLE_P[i % 8][int(digit)]]
    return c == 0

# --- OTP & TWILIO LOGIC ---
import random
from twilio.rest import Client

def generate_otp() -> str:
    """Generate a random 6-digit OTP."""
    return str(random.randint(100000, 999999))

def send_twilio_otp(to_number: str, otp: str, sid: str, token: str, from_number: str):
    """Send OTP via Twilio SMS."""
    try:
        client = Client(sid, token)
        message = client.messages.create(
            body=f"Your AI Health Dashboard verification code is: {otp}. Do not share this with anyone.",
            from_=from_number,
            to=to_number
        )
        return message.sid, None
    except Exception as e:
        print(f"Twilio Send Error: {e}")
        return None, str(e)
