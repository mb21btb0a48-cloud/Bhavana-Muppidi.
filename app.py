# Import streamlit for the main UI
import streamlit as st
# Import pandas for dataframe creation
import pandas as pd
# Import OpenAI class for API interaction
from openai import OpenAI

# Import Pydantic models from the custom models module
from models import HealthProfile
# Import utility functions from the custom utils module
from utils import extract_pdf_text, extract_docx_text, get_image_base64, load_lottieurl, transcribe_audio, generate_audio_summary, fetch_local_health_restaurants, validate_aadhar, generate_otp, send_twilio_otp, get_location_name
from db import init_db, save_patient_report, get_patient_history, check_and_deduct_token, save_user
from streamlit_geolocation import streamlit_geolocation
from ui import hide_default_ui, apply_global_css, show_splash_screen, styled_header, render_top_banner, render_diagnostic_table, render_nutrient_pie_chart, render_body_progress_chart, render_chart_placeholder, render_auth_screen, close_auth_card
import plotly.graph_objects as go
import json
from fpdf import FPDF
import io
import time

# Initialize SQLite database
init_db()

# Setup the initial page configuration, must be the first Streamlit command
st.set_page_config(page_title="AI Health Dashboard", page_icon="🧬", layout="wide")



# ---------------------------------------------------------
# API KEY CONFIGURATION
# ---------------------------------------------------------
import os

# Securely grab the API key from Streamlit Secrets or OS Environment Variables
try:
    if "OPENAI_API_KEY" in st.secrets:
        YOUR_OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
    else:
        YOUR_OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
        
    if not YOUR_OPENAI_API_KEY:
        raise ValueError("Key not found")
except Exception:
    st.error("⚠️ OPENAI_API_KEY is missing! Please configure it securely in your Hosting Platform's Environment Variables or Secrets settings.")
    st.stop()

# Get SerpAPI Key dynamically for Advanced Menu Crawling
try:
    if "SERPAPI_KEY" in st.secrets:
        YOUR_SERPAPI_KEY = st.secrets["SERPAPI_KEY"]
    else:
        YOUR_SERPAPI_KEY = os.environ.get("SERPAPI_KEY", "")
except Exception:
    YOUR_SERPAPI_KEY = ""

# Apply function to hide default Streamlit UI elements
hide_default_ui()

# Display the initial custom splash screen logic
show_splash_screen()

# Apply the global CSS styling automatically integrated with Streamlit settings
apply_global_css()

# --- INITIALIZE CHAT STATE & LOGIC ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hi! I'm your AI Dietitian. Do you have any questions about your health, diet, or dashboard?"}]
if "current_profile" not in st.session_state:
    st.session_state.current_profile = None
if "audio_summary_bytes" not in st.session_state:
    st.session_state.audio_summary_bytes = None
if "consumed_log" not in st.session_state:
    st.session_state.consumed_log = []
if "real_restaurants" not in st.session_state:
    st.session_state.real_restaurants = []

# --- AUTHENTICATION STATE ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "otp_sent" not in st.session_state:
    st.session_state.otp_sent = False
if "generated_otp" not in st.session_state:
    st.session_state.generated_otp = None
if "verified_mobile" not in st.session_state:
    st.session_state.verified_mobile = None

def handle_chat():
    user_q = st.session_state.user_question
    if not user_q.strip(): return
    
    # Append user question
    st.session_state.messages.append({"role": "user", "content": user_q})
    
    # Fetch AI response
    try:
        from openai import OpenAI
        client = OpenAI(api_key=YOUR_OPENAI_API_KEY)
        # Create a condensed conversation history
        history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages]
        
        sys_msg = "You are a friendly, highly concise Gold-Medalist AI Dietitian. You help the user understand their diet, health issues, and provide highly specific actionable medical nutrition advice. Keep responses extremely brief and use emojis."
        if "latest_profile" in st.session_state:
            sys_msg += f"\n\nContext of the User's Latest Generated Report:\n{st.session_state.latest_profile}"
            
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": sys_msg},
                *history
            ]
        )
        st.session_state.messages.append({"role": "assistant", "content": response.choices[0].message.content})
    except Exception as e:
        st.session_state.messages.append({"role": "assistant", "content": "Oops! Make sure your OpenAI API key is valid."})
        
    # Clear input box
    st.session_state.user_question = ""

# --- AUTHENTICATION GATE ---
if not st.session_state.authenticated:
    aadhar_input, mobile_input, otp_input = render_auth_screen()
    
    if not st.session_state.otp_sent:
        if st.button("🚀 Send Verification Code", type="primary", use_container_width=True):
            if not validate_aadhar(aadhar_input):
                st.error("❌ Invalid Aadhar Number. Please enter a valid 12-digit number.")
            elif not mobile_input or len(mobile_input) < 10:
                st.error("❌ Please enter a valid mobile number.")
            else:
                otp = generate_otp()
                st.session_state.generated_otp = otp
                st.session_state.verified_mobile = mobile_input
                st.session_state.verified_aadhar = aadhar_input
                
                # Twilio Dispatch
                sid = st.secrets["TWILIO_ACCOUNT_SID"]
                token = st.secrets["TWILIO_AUTH_TOKEN"]
                from_num = st.secrets["TWILIO_PHONE_NUMBER"]
                
                # Force Indian Country Code if missing
                if not mobile_input.startswith("+"):
                    if not mobile_input.startswith("91"):
                        formatted_mobile = "+91" + mobile_input
                    else:
                        formatted_mobile = "+" + mobile_input
                else:
                    formatted_mobile = mobile_input
                
                with st.spinner("Sending secure OTP via Twilio..."):
                    success, error_msg = send_twilio_otp(formatted_mobile, otp, sid, token, from_num)
                    if success:
                        st.session_state.otp_sent = True
                        st.rerun()
                    else:
                        st.error(f"❌ Twilio API Error: {error_msg}")
                        st.info("💡 Note: If you are using a Twilio Free Trial, Twilio blocks sending to unverified numbers.")
    else:
        if st.button("✅ Verify & Enter Dashboard", type="primary", use_container_width=True):
            if otp_input == st.session_state.generated_otp:
                st.session_state.authenticated = True
                save_user(st.session_state.verified_aadhar, st.session_state.verified_mobile)
                st.success("✔ Identity Verified Successfully!")
                time.sleep(1)
                st.rerun()
            else:
                st.error("❌ Incorrect OTP. Please try again.")
        
        if st.button("⬅️ Back / Change Number", use_container_width=True):
            st.session_state.otp_sent = False
            st.rerun()
            
    close_auth_card()
    st.stop() # Halt execution here if not authenticated

# --- TOP NAVIGATION & HELP CHAT ---
# We create a column layout designed to push the Help button to the absolute top right
nav_cols = st.columns([9, 2])

with nav_cols[1]:
    # St.popover creates a clickable button that drops down the component
    with st.popover("💬 Help / Chat", use_container_width=True):
        st.markdown("<h4 style='color:#111827; font-weight:800; margin-top:0;'>🤖 AI Dietitian</h4>", unsafe_allow_html=True)
        # Chat history container
        chat_box = st.container(height=350)
        with chat_box:
            for msg in st.session_state.messages:
                # Use standard chat styling for roles
                st.chat_message(msg["role"]).write(msg["content"])
        
        # Standard text input triggered on 'Enter'
        st.text_input("Ask a question (Press Enter)...", key="user_question", on_change=handle_chat)

# Load the Lottie animation for the header
lottie_anim = load_lottieurl("https://lottie.host/80ebbeeb-4c54-47af-befe-a17fdb03936c/2j4R2R9k8I.json")

# Render the top banner including title and animation
render_top_banner(lottie_anim)

# --- Main Input Area ---
# Insert a line break for layout spacing
st.markdown("<br>", unsafe_allow_html=True)

# Create a radio buttons group to choose the input method
input_method = st.radio("Choose how to provide your health data:", 
                        ["✍️ Manual Entry", "📄 Upload Medical Report", "📸 Take a Picture"], 
                        horizontal=True)

# Set the header text dynamically based on the chosen input method
header_text = "Your Report Analysis" if input_method != "✍️ Manual Entry" else "Start Your Analysis"

# Create a styled container for the input forms
with st.container():
    # Inject HTML for the styled input container
    st.markdown(f"""
    <div style="background: #ffffff; border: 1px solid #e5e7eb; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.01); border-radius: 16px; padding: 25px; margin-bottom: 25px;">
    """, unsafe_allow_html=True)

    # Render a horizontal dividing line inside the container
    st.markdown("<hr style='border:1px solid #eee;'>", unsafe_allow_html=True)
    
    # --- Clinical Context Row ---
    st.markdown("<p style='color:#6b7280; font-size:12px; font-weight:700; text-transform:uppercase; margin-bottom:10px; letter-spacing:0.5px;'>🧬 Clinical Context & Location</p>", unsafe_allow_html=True)
    ext_col1, ext_col2, ext_col3 = st.columns([1.5, 2, 2.5], gap="medium")
    with ext_col1:
        report_language = st.selectbox("Preferred Language", ["English", "Telugu", "Hindi"])
    with ext_col2:
        user_meds = st.text_input("Current Medications", placeholder="Optional (e.g. Statins)")
    with ext_col3:
        manual_location = st.text_input("Manually Enter Address", placeholder="e.g. 123 Main St, Hyderabad 500001")
        
        st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
        location_data = streamlit_geolocation()
        user_lat = location_data.get('latitude') if location_data else None
        user_lng = location_data.get('longitude') if location_data else None
        
        # Sleek GPS Badge
        if user_lat and user_lng:
            st.markdown("""
            <div style="background: #ecfdf5; border: 1px solid #10b981; border-radius: 30px; padding: 10px 18px; display: flex; align-items: center; gap: 8px; box-shadow: 0 4px 6px -4px rgba(16,185,129,0.25); max-width: 250px;">
                <span style="font-size: 16px;">📍</span>
                <span style="color: #065f46; font-size: 13px; font-weight: 800;">Location Active</span>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background: #eff6ff; border: 1px solid #3b82f6; border-radius: 30px; padding: 10px 18px; display: flex; align-items: center; gap: 8px; box-shadow: 0 4px 6px -4px rgba(59,130,246,0.25); max-width: 250px;">
                <span style="font-size: 16px;">📡</span>
                <span style="color: #1e40af; font-size: 13px; font-weight: 700;">Find Nearby Dietitian</span>
            </div>
            """, unsafe_allow_html=True)
    
    # Universal Inputs Complete
    
    # Keep patient_id for internal database continuity, but completely hide it from the UI.
    patient_id = st.session_state.get('verified_aadhar')



    st.markdown("<hr style='border:1px solid #eee;'>", unsafe_allow_html=True)

    # Initialize variables to hold user inputs
    user_disease = None
    document_text = None
    image_base64 = None
    uploaded_file = None
    camera_photo = None
    audio_bytes = None

    # Handle inputs for Manual Entry mode
    if input_method == "✍️ Manual Entry":
        # Create two columns for manual inputs
        col1, col2 = st.columns(2)
        # Text input for the specific disease
        with col1:
            user_disease = st.text_input("Enter Disease or Condition", placeholder="e.g., Diabetes, Hypertension")
            audio_bytes = st.audio_input("🎙️ Or speak your disease/symptoms:")
        # Number input for user age
        with col2:
            user_age = st.number_input("Enter your Age", min_value=1, max_value=120, value=30)
            
    # Handle inputs for Upload Medical Report mode
    elif input_method == "📄 Upload Medical Report":
        # Number input for user age
        user_age = st.number_input("Enter your Age", min_value=1, max_value=120, value=30)
        # File uploader for medical documents and images
        uploaded_file = st.file_uploader("Upload your CURRENT lab report or diagnosis document", type=["pdf", "docx", "png", "jpg", "jpeg"])
        past_uploaded_file = st.file_uploader("Upload a PAST report for Differential Comparison (Optional)", type=["pdf", "docx"])
        # Process the uploaded file
        if uploaded_file:
            # Extract the file extension to determine the file type
            file_extension = uploaded_file.name.split('.')[-1].lower()
            # If the file is a PDF, extract its text
            if file_extension == "pdf":
                document_text = extract_pdf_text(uploaded_file)
                st.success("PDF Extracted Successfully!")
            # If the file is a DOCX, extract its text
            elif file_extension == "docx":
                document_text = extract_docx_text(uploaded_file)
                st.success("DOCX Extracted Successfully!")
            # If the file is an image, encode it to base64
            elif file_extension in ["png", "jpg", "jpeg"]:
                image_base64 = get_image_base64(uploaded_file)
                st.image(uploaded_file, caption="Preview of Uploaded Report", width=350)
                
    # Handle inputs for Take a Picture mode
    elif input_method == "📸 Take a Picture":
        # Number input for user age
        user_age = st.number_input("Enter your Age", min_value=1, max_value=120, value=30)
        # Camera input widget for taking pictures
        camera_photo = st.camera_input("Take a clear picture of your physical medical report")
        # Process the picture if available
        if camera_photo:
            image_base64 = get_image_base64(camera_photo)

    # Close the styled container HTML
    st.markdown("</div>", unsafe_allow_html=True)

# Add Consent
st.markdown("<br>", unsafe_allow_html=True)
consent = st.checkbox("✅ I acknowledge that this AI Dashboard is for educational purposes and is not a substitute for professional medical diagnosis.")

# Render the primary action button for recommendations
st.markdown("<br>", unsafe_allow_html=True)
if st.button("Get Recommendations", type="primary", use_container_width=True):
    # Define flags to hold readiness status and error message
    ready_to_process = False
    error_msg = ""
    
    # Validate API Key presence
    if not consent:
        error_msg = "Please acknowledge the medical disclaimer by checking the box."
    elif YOUR_OPENAI_API_KEY.startswith("sk-") == False or len(YOUR_OPENAI_API_KEY) < 20:
        error_msg = "Please paste your valid OpenAI API Key into the `app.py` code file and SAVE!"
    # Validate logic based on input mode selection
    else:
        # Validate that a disease was entered or spoken in manual mode
        if input_method == "✍️ Manual Entry" and not user_disease and not audio_bytes:
            error_msg = "Please enter a disease or condition, or record it via the microphone."
        # Validate that a document was uploaded in upload mode
        elif input_method == "📄 Upload Medical Report" and not uploaded_file:
            error_msg = "Please upload a current document to proceed."
        # Validate that a picture was taken in camera mode
        elif input_method == "📸 Take a Picture" and not camera_photo:
            error_msg = "Please take a picture of your document to proceed."
        # Set readiness to true if validations pass
        else:
            ready_to_process = True
            
    # Display the error message if the form is not ready
    if not ready_to_process:
        st.error(error_msg)
    # Proceed when everything is valid
    else:
        # TOKEN PAYWALL CHECK (Temporarily Disabled for Testing)
        # if patient_id:
        #     has_tokens = check_and_deduct_token(patient_id)
        #     if not has_tokens:
        #         st.error("🔒 **PREMIUM FEATURE LOCKED**")
        #         st.markdown("""
        #         <div style="text-align:center; padding: 40px; background: #fffbfa; border: 2px solid #fda4af; border-radius: 16px; margin-bottom: 25px;">
        #             <h2 style="color:#e11d48; margin-top:0;">0 Tokens Remaining</h2>
        #             <p style="color:#4c0519; font-size:16px;">You have exhausted your free advanced clinical analysis.</p>
        #             <button style="background:#e11d48; color:white; padding: 12px 24px; border:none; border-radius:8px; font-weight:bold; font-size:16px; cursor:pointer; box-shadow: 0 4px 6px rgba(225,29,72,0.3);">💳 Upgrade to Pro - $19.99/mo</button>
        #             <p style="color:#4c0519; font-size:12px; margin-top: 15px; opacity: 0.7;">Secure payment processed via Stripe</p>
        #         </div>
        #         """, unsafe_allow_html=True)
        #         st.stop()

        # Initialize the OpenAI client
        client = OpenAI(api_key=YOUR_OPENAI_API_KEY)
        


        # Parse Past Document for Differential Comparison
        past_report_context = ""
        if input_method == "📄 Upload Medical Report" and 'past_uploaded_file' in locals() and past_uploaded_file:
            try:
                past_ext = past_uploaded_file.name.split('.')[-1].lower()
                if past_ext == "pdf": 
                    past_report_context = f"\nPAST REPORT FOR COMPARISON:\n{extract_pdf_text(past_uploaded_file)}\nCompare the current report to this past report to strictly define the 'trend' status (e.g., Improved, Degraded) for each diagnostic."
                elif past_ext == "docx":
                    past_report_context = f"\nPAST REPORT FOR COMPARISON:\n{extract_docx_text(past_uploaded_file)}\nCompare the current report to this past report to strictly define the 'trend' status (e.g., Improved, Degraded) for each diagnostic."
            except:
                pass

        # Create a temporary empty component for displaying a loading state
        loader_placeholder = st.empty()
        # Render the custom loading animation markdown
        loader_placeholder.markdown("""
        <div style="text-align:center; padding: 40px; background: #ffffff; border-radius: 20px; border: 1px solid #e5e7eb; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);">
          <div style="font-size: 55px; animation: slide 2s linear infinite; display:inline-block;">🥦🥑🥩🥗🫐🍗🍎</div>
          <div class="loading-text-container">
            <div class="loading-text lt-1">Querying Premium Paywall...</div>
            <div class="loading-text lt-2">Evaluating Longitudinal Diagnostics...</div>
            <div class="loading-text lt-3">Calculating Macronutrient Ratios...</div>
            <div class="loading-text lt-4">Formulating AI Meal Reroll Arrays...</div>
          </div>
          <style>@keyframes slide { 0% {transform: translateX(30%); opacity:0.3;} 50% {opacity:1;} 100% {transform: translateX(-30%); opacity:0.3;} }</style>
        </div>
        """, unsafe_allow_html=True)
        
        try:
            # Process Audio if present
            if input_method == "✍️ Manual Entry" and audio_bytes and not user_disease:
                user_disease = transcribe_audio(client, audio_bytes.getvalue())
                st.info(f"🎙️ Transcribed from audio: {user_disease}")

            # Process User Location Dynamically
            user_location_context = "Global/International"
            final_city_for_search = None
            
            if manual_location:
                user_location_context = manual_location
                final_city_for_search = manual_location
                st.info(f"🌍 Culturally adapting meal plan and scanning restaurants for delivery address: **{manual_location}**")
            elif user_lat and user_lng:
                detected_loc = get_location_name(user_lat, user_lng)
                if detected_loc:
                    user_location_context = detected_loc
                    st.info(f"🌍 Culturally adapting meal plan for your GPS location: **{detected_loc}**")

            # VERY ADVANCED: Crawl real nearby restaurants strictly with GPS coords or Manual City
            # Check context for restaurant search (either via GPS or manual City input)
            st.session_state.real_restaurants = []
            if manual_location or (user_lat and user_lng):
                with st.spinner("📍 Web Crawler extracting real menus..."):
                    # If manual location is provided, ignore exact lat/lng to force city-wide search
                    s_lat = None if manual_location else user_lat
                    s_lng = None if manual_location else user_lng
                    st.session_state.real_restaurants = fetch_local_health_restaurants(user_disease if user_disease else "healthy", s_lat, s_lng, final_city_for_search, YOUR_SERPAPI_KEY)

            # Define the system prompt for the AI's clinical personality
            sys_message = f"""
            You are a highly prestigious, Gold-Medalist MBBS Doctor. You specialize in clinical nutrition and diagnostic interpretation. 
            Your goal is to provide 100% accurate health education based on user reports. 
            As a gold medalist, your advice is extremely specific:
            - STRICT PRIVACY COMPLIANCE: Focus EXCLUSIVELY on the clinical diagnostic values, ignore PII.
            - Provide highly specific foods to eat and specifically named items to avoid with clinical reasons.
            - CRITICAL FOR DIAGNOSTICS: You MUST output a completely separate `DiagnosticTest` object in the array for EVERY SINGLE individual biomarker. 
            - Extraction: Extract the EXACT 'patient_value' and 'value_range' found in the report.
            - SEVERITY SCORING (0-100): This is a POSITIONAL score for the UI gauge. You MUST set:
              - 50 for all 'Normal' or 'Stable' results.
              - 15 for 'Low' or 'Deficient' results.
              - 85 for 'High', 'Elevated', or 'Needs Attention' results.
              - (Optional: Use a precise 0-100 score if the value is extremely far from the range).
            - 🌍 CULTURAL PALATE & LOCATION: The user is currently located in '{user_location_context}'. You MUST adapt the suggested foods, ingredients, and dishes strictly to the local cuisine, cultural norms, and locally available ingredients of this region. For example, if in Telangana, India, recommend regional items; if in the USA, recommend appropriate local healthy items seamlessly.
            - DIETARY PREFERENCE: The user has selected a {st.session_state.get('master_diet_pref', 'Vegetarian')} diet. You MUST generate the 7-day meal plan *exclusively* for this preference.
            - NEW: Generate a 'weekly_meal_plan' which is a list of EXACTLY 7 distinct DailyMealOptions (one for each day from Mon to Sun in order: Mon, Tue, Wed, Thu, Fri, Sat, Sun). EVERY day must be present.
            - CRITICAL QUANTITY: You MUST provide EXACTLY 3 to 4 distinct 'MealItem' objects for EVERY meal (breakfast, lunch, dinner, snacks) for each day without exception.
            - CRITICAL DATA STRUCTURE: Each 'MealItem' MUST include: 'name' (concise, 3-5 words), 'calories' (int), 'protein' (int, grams), 'carbs' (int, grams), 'fats' (int, grams), and 'water_ml' (int, estimated hydration). 
            - Example MealItem: {{"name": "Moong Dal Khichdi", "calories": 320, "protein": 12, "carbs": 45, "fats": 8, "water_ml": 250}}.
            - 🌍 MULTILINGUAL REQUIREMENT: You MUST output all generated text, strings, and descriptions strictly in {report_language}. Return all JSON keys in English, but output all JSON VALUES strictly in {report_language}.
            - Your tone is professional, authoritative, yet encouraging.
            """

            medication_context = f"The user is currently taking the following medications: '{user_meds}'. CRITICALLY: Cross-reference these drugs with dietary guidelines and heavily flag any chemical food-drug interactions in the 'avoided_foods' section." if user_meds else ""
            sys_message += medication_context if medication_context else ""
            
            # Construct variables based on the active input mode
            if input_method == "✍️ Manual Entry":
                # Create the prompt string for manual text format
                user_msg = f"The user is {user_age} years old and has the condition: '{user_disease}'. \n{medication_context}\n{past_report_context}\nAs a professional Gold-Medalist Doctor, identify every relevant diagnostic test. Extract values, standard ranges, and interpretations. Provide nutritional needs, macro calculations, foods, strict avoided foods, and strict daily meal plans."
                # Define the label used in the final report template
                disease_label = user_disease
            elif image_base64:
                # Structure the JSON array message needed for vision inputs
                user_msg = [
                    {"type": "text", "text": f"The user is {user_age} years old. \n{medication_context}\n{past_report_context}\nAs a Gold-Medalist MBBS Doctor, analyze this medical report image with 100% accuracy. Extract every single lab value entry. Provide nutritional requirements, macro calculations, foods, specific avoided items, and strict daily meal plans."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                ]
                # Defing the label used in the final report template
                disease_label = "Report Analysis"
            else:
                # Create the prompt string for passing extracted text
                user_msg = f"The user is {user_age} years old. \n{medication_context}\n{past_report_context}\nAs a Gold-Medalist MBBS Doctor, analyze this extracted medical report text: '{document_text}'. Extract every lab result accurately. Provide inferred conditions, nutritional needs, macro calculations, foods, avoided items, and strict daily meal plans."
                

                
            # Perform the Chat completions request to generate structured output
            response = client.beta.chat.completions.parse(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": sys_message},
                    {"role": "user", "content": user_msg}
                ],
                # Add maximum tokens to prevent 7th day cutoff
                max_tokens=16000,
                # Pass the Pydantic schema class to enforce the output format
                response_format=HealthProfile,
            )
            
            # Extract the fully validated, parsed output from the API response
            st.session_state.current_profile = response.choices[0].message.parsed
            
            # Save the profile to session state so the chatbot has full context
            st.session_state.latest_profile = st.session_state.current_profile.model_dump_json()
            
            # Save to Database if tracking identifier is provided
            if patient_id:
                save_patient_report(patient_id, st.session_state.latest_profile)

            # Generate TTS Summary (Audio)
            nut_focus = st.session_state.current_profile.nutrients[0].nutrient_name if st.session_state.current_profile.nutrients else "your diet"
            audio_text = f"Your personalized health analysis is complete. Our top priority is focusing on {nut_focus}. Please review the specific dietary guidelines below."
            st.session_state.audio_summary_bytes = generate_audio_summary(client, audio_text)
            
            # Remove the loader animation once processing finishes
            loader_placeholder.empty()

        # Gracefully handle API response mapping errors if any
        except Exception as e:
            st.error(f"An error occurred. Diagnostics: {e}")

# --- PERSISTENT RENDERING BLOCK (Outside of Session Button) ---
if st.session_state.current_profile:
    profile = st.session_state.current_profile
    audio_summary_bytes = st.session_state.audio_summary_bytes
    real_restaurants = st.session_state.real_restaurants

    try:
        # 1. PDF Download Section - Comprehensive Clinical Report
        def generate_pdf(prof):
            # Safety wrapper: strip all non-Latin-1 characters (emojis, special Unicode)
            def safe(text):
                return str(text).encode('latin-1', 'ignore').decode('latin-1')

            pdf = FPDF()
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.add_page()

            # --- COVER / TITLE ---
            pdf.set_font("helvetica", "B", 22)
            pdf.cell(0, 15, "AI Health Dashboard", ln=True, align="C")
            pdf.set_font("helvetica", "", 13)
            pdf.cell(0, 8, "Comprehensive Clinical Summary Report", ln=True, align="C")
            pdf.set_font("helvetica", "", 11)
            pdf.cell(0, 8, f"Generated for: {patient_id if patient_id else 'Guest Patient'}", ln=True, align="C")
            pdf.cell(0, 8, f"Overall Diet Adherence Score: {prof.health_score} / 100", ln=True, align="C")
            pdf.ln(5)
            pdf.set_draw_color(37, 99, 235)
            pdf.set_line_width(0.8)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(8)

            # --- SECTION 1: DIAGNOSTICS ---
            pdf.set_font("helvetica", "B", 15)
            pdf.set_text_color(15, 23, 42)
            pdf.cell(0, 10, "Diagnostic Report Values", ln=True)
            pdf.set_font("helvetica", "", 9)
            pdf.set_text_color(80, 80, 80)
            # Table Header
            pdf.set_fill_color(241, 245, 249)
            pdf.set_font("helvetica", "B", 9)
            pdf.cell(45, 7, "Test Name", 1, 0, "L", True)
            pdf.cell(25, 7, "Value", 1, 0, "C", True)
            pdf.cell(30, 7, "Ref. Range", 1, 0, "C", True)
            pdf.cell(20, 7, "Status", 1, 0, "C", True)
            pdf.cell(70, 7, "Interpretation", 1, 1, "L", True)
            pdf.set_font("helvetica", "", 8)
            for d in prof.diagnostics:
                pdf.cell(45, 6, safe(d.test_name)[:28], 1, 0, "L")
                pdf.cell(25, 6, safe(d.patient_value)[:15], 1, 0, "C")
                pdf.cell(30, 6, safe(d.value_range)[:18], 1, 0, "C")
                if "high" in d.status.lower():
                    pdf.set_text_color(185, 28, 28)
                elif "low" in d.status.lower():
                    pdf.set_text_color(202, 138, 4)
                else:
                    pdf.set_text_color(22, 101, 52)
                pdf.cell(20, 6, safe(d.status), 1, 0, "C")
                pdf.set_text_color(80, 80, 80)
                pdf.cell(70, 6, safe(d.interpretation)[:42], 1, 1, "L")
            pdf.ln(6)

            # --- SECTION 2: KEY NUTRIENTS ---
            pdf.set_font("helvetica", "B", 15)
            pdf.set_text_color(15, 23, 42)
            pdf.cell(0, 10, "Key Nutritional Focus", ln=True)
            pdf.set_font("helvetica", "", 10)
            pdf.set_text_color(80, 80, 80)
            for nut in prof.nutrients:
                pdf.set_font("helvetica", "B", 10)
                pdf.cell(0, 7, safe(f"  {nut.nutrient_name}  -  {nut.status}"), ln=True)
                pdf.set_font("helvetica", "", 9)
                pdf.multi_cell(0, 5, safe(f"    {nut.description}"))
                pdf.ln(2)
            pdf.ln(4)

            # --- SECTION 3: RECOMMENDED FOODS ---
            pdf.set_font("helvetica", "B", 15)
            pdf.set_text_color(15, 23, 42)
            pdf.cell(0, 10, "Recommended Food Sources", ln=True)
            pdf.set_font("helvetica", "", 10)
            pdf.set_text_color(80, 80, 80)
            for food in prof.foods:
                pdf.cell(0, 7, safe(f"  {food.category_name}: {food.examples}"), ln=True)
            pdf.ln(4)

            # --- SECTION 4: FOODS TO AVOID ---
            pdf.set_font("helvetica", "B", 15)
            pdf.set_text_color(185, 28, 28)
            pdf.cell(0, 10, "Items Strictly to Avoid", ln=True)
            pdf.set_font("helvetica", "", 10)
            pdf.set_text_color(80, 80, 80)
            for item in prof.avoided_foods:
                pdf.set_font("helvetica", "B", 10)
                pdf.cell(0, 7, safe(f"  {item.food_name}"), ln=True)
                pdf.set_font("helvetica", "", 9)
                pdf.multi_cell(0, 5, safe(f"    Reason: {item.reason}"))
                pdf.ln(2)
            pdf.ln(4)

            # --- SECTION 5: MACRONUTRIENT TARGETS ---
            pdf.set_font("helvetica", "B", 15)
            pdf.set_text_color(15, 23, 42)
            pdf.cell(0, 10, "Daily Macronutrient Targets", ln=True)
            pdf.set_font("helvetica", "", 11)
            pdf.set_text_color(80, 80, 80)
            pdf.cell(0, 8, f"  Calories: {prof.daily_macros.calories} kcal / day", ln=True)
            pdf.cell(0, 8, f"  Protein: {prof.daily_macros.protein}g  |  Carbs: {prof.daily_macros.carbs}g  |  Fats: {prof.daily_macros.fats}g", ln=True)
            pdf.ln(6)

            # --- SECTION 6: 7-DAY MEAL PLAN ---
            pdf.set_font("helvetica", "B", 15)
            pdf.set_text_color(15, 23, 42)
            pdf.cell(0, 10, "7-Day Weekly Meal Plan", ln=True)
            day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            meal_labels = ["Breakfast", "Lunch", "Dinner", "Snacks"]
            for d_idx, day_plan in enumerate(prof.weekly_meal_plan):
                if d_idx < len(day_names):
                    pdf.set_font("helvetica", "B", 12)
                    pdf.set_fill_color(239, 246, 255)
                    pdf.cell(0, 8, f"  {day_names[d_idx]}", ln=True, fill=True)
                    day_items = day_plan.meal_plan
                    meals = [day_items.breakfast, day_items.lunch, day_items.dinner, day_items.snacks]
                    for m_idx, meal_list in enumerate(meals):
                        pdf.set_font("helvetica", "BI", 10)
                        pdf.set_text_color(37, 99, 235)
                        pdf.cell(0, 7, f"    {meal_labels[m_idx]}:", ln=True)
                        pdf.set_font("helvetica", "", 9)
                        pdf.set_text_color(80, 80, 80)
                        for m_item in meal_list:
                            name = safe(m_item.name) if hasattr(m_item, "name") else safe(str(m_item))
                            cal = m_item.calories if hasattr(m_item, "calories") else ""
                            prot = m_item.protein if hasattr(m_item, "protein") else ""
                            carb = m_item.carbs if hasattr(m_item, "carbs") else ""
                            fat = m_item.fats if hasattr(m_item, "fats") else ""
                            pdf.cell(0, 6, f"      - {name}  ({cal} kcal | P:{prot}g | C:{carb}g | F:{fat}g)", ln=True)
                    pdf.ln(3)
            pdf.ln(4)

            # --- SECTION 7: GROCERY LIST ---
            pdf.set_font("helvetica", "B", 15)
            pdf.set_text_color(15, 23, 42)
            pdf.cell(0, 10, "Grocery Shopping List", ln=True)
            pdf.set_font("helvetica", "", 10)
            pdf.set_text_color(80, 80, 80)
            for cat in prof.grocery_list:
                pdf.set_font("helvetica", "B", 10)
                pdf.cell(0, 7, safe(f"  {cat.category_name}:"), ln=True)
                pdf.set_font("helvetica", "", 9)
                for gi in cat.items:
                    pdf.cell(0, 6, safe(f"    - {gi}"), ln=True)
                pdf.ln(2)
            pdf.ln(4)

            # --- SECTION 8: HYDRATION ---
            pdf.set_font("helvetica", "B", 15)
            pdf.set_text_color(15, 23, 42)
            pdf.cell(0, 10, "Hydration Goal", ln=True)
            pdf.set_font("helvetica", "", 12)
            pdf.set_text_color(80, 80, 80)
            pdf.cell(0, 8, safe(f"  Recommended Daily Target: {prof.hydration}"), ln=True)
            pdf.ln(8)

            # --- FOOTER ---
            pdf.set_draw_color(37, 99, 235)
            pdf.set_line_width(0.5)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(5)
            pdf.set_font("helvetica", "I", 9)
            pdf.set_text_color(148, 163, 184)
            pdf.cell(0, 6, "This report is generated by the AI Health Dashboard for educational purposes only.", ln=True, align="C")
            pdf.cell(0, 6, "It is not a substitute for professional medical diagnosis.", ln=True, align="C")

            return bytes(pdf.output())

        pdf_bytes = generate_pdf(profile)
        st.download_button(
            label="📄 Download Official Medical PDF",
            data=pdf_bytes,
            file_name=f"Health_Report_{patient_id if patient_id else 'Guest'}.pdf",
            mime="application/pdf"
        )

        # Render Headings
        styled_header("📑 Diagnostic Report Values")

        # Render the custom diagnostic table with visual status gauges
        if profile.diagnostics:
            is_manual = (input_method == "✍️ Manual Entry")
            render_diagnostic_table(profile.diagnostics, is_manual=is_manual)
        
        # Render a custom heading for Nutritional Focus
        if profile.nutrients:
            styled_header("🧪 Key Nutritional Focus")
            nut_cols = st.columns(len(profile.nutrients))
            for i, nut in enumerate(profile.nutrients):
                with nut_cols[i % len(nut_cols)]:
                    status_color = "#2e7d32" if "increase" in nut.status.lower() or "need" in nut.status.lower() else "#c62828"
                    st.markdown(f"""
                    <div class="hover-card" style="border-left: 6px solid {status_color}; text-align: center; margin-bottom: 15px;">
                        <h4 style="margin:0; color:#111827; font-weight:700;">{nut.nutrient_name}</h4>
                        <p style="margin:0; font-weight:800; color:{status_color}; text-transform:uppercase; font-size:13px; margin-top:4px;">{nut.status}</p>
                        <details><summary>ℹ️ View Clinical Reasoning</summary><p>{nut.description}</p></details>
                    </div>
                    """, unsafe_allow_html=True)
        
        # Render a custom heading for Recommended Foods
        if profile.foods:
            styled_header("🥗 Recommended Food Sources")
            food_cols = st.columns(min(len(profile.foods), 4))
            for i, food in enumerate(profile.foods):
                with food_cols[i % len(food_cols)]:
                    st.markdown(f"""
                    <div class="hover-card" style="text-align: center; margin-bottom: 20px;">
                        <div style="font-size: 60px; line-height: 1;">{food.emoji}</div>
                        <h3 style="margin-top: 15px; margin-bottom: 8px; color:#111827; font-weight:800; font-size: 20px;">{food.category_name}</h3>
                        <p style="color:#4b5563; font-size:14px; line-height:1.5;">{food.examples}</p>
                    </div>
                    """, unsafe_allow_html=True)
        
        # Render a custom heading for Foods to Avoid
        if profile.avoided_foods:
            styled_header("🚫 Items strictly to Avoid")
            for item in profile.avoided_foods:
                st.markdown(f"""
                <div class="hover-card avoid-card" style="margin-bottom: 15px;">
                    <div style="font-size: 45px;">{item.emoji}</div>
                    <div style="width:100%;">
                        <h4 style="margin: 0; color: #b91c1c; font-weight: 800; font-size: 18px;">Strictly Avoid: {item.food_name}</h4>
                        <details><summary>ℹ️ View Clinical Reasoning</summary><p>{item.reason}</p></details>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("""
        <style>
        .macro-card { 
            background: #ffffff; border: 1px solid #e5e7eb; border-radius: 16px; 
            padding: 20px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); 
            transition: transform 0.2s ease, box-shadow 0.2s ease;
            text-align: center; height: 100%;
        }
        .macro-card:hover { transform: translateY(-4px); box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); }
        .macro-label { color: #374151; font-weight: 800; font-size: 14px; text-transform: uppercase; margin-bottom: 5px; letter-spacing: 0.5px; }
        </style>
        """, unsafe_allow_html=True)
        
        styled_header("🔥 Daily Macronutrient Targets")
        m_col1, m_col2, m_col3, m_col4 = st.columns(4)
        with m_col1:
            st.markdown(f"<div class='macro-card'><p class='macro-label' style='color:#1e293b;'>Energy Goal</p><h2 style='margin:10px 0 0 0; color:#1e293b; font-size:32px; font-weight:900;'>{profile.daily_macros.calories}</h2><p style='margin:0; color:#64748b; font-size:14px; font-weight:700;'>kcal / day</p></div>", unsafe_allow_html=True)
        with m_col2:
            st.markdown(f"<div class='macro-card'><p class='macro-label' style='color:#ea580c;'>Protein</p><h2 style='margin:10px 0 0 0; color:#ea580c; font-size:32px; font-weight:900;'>{profile.daily_macros.protein}g</h2><p style='margin:0; color:#64748b; font-size:14px; font-weight:700;'>Target Intake</p></div>", unsafe_allow_html=True)
        with m_col3:
            st.markdown(f"<div class='macro-card'><p class='macro-label' style='color:#2563eb;'>Carbohydrate</p><h2 style='margin:10px 0 0 0; color:#2563eb; font-size:32px; font-weight:900;'>{profile.daily_macros.carbs}g</h2><p style='margin:0; color:#64748b; font-size:14px; font-weight:700;'>Target Intake</p></div>", unsafe_allow_html=True)
        with m_col4:
            st.markdown(f"<div class='macro-card'><p class='macro-label' style='color:#059669;'>Healthy Fats</p><h2 style='margin:10px 0 0 0; color:#059669; font-size:32px; font-weight:900;'>{profile.daily_macros.fats}g</h2><p style='margin:0; color:#64748b; font-size:14px; font-weight:700;'>Target Intake</p></div>", unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)

        styled_header("📅 7-Day Interactive Weekly Meal Calendar")
        
        # Section-Internal Diet Control
        m_main_col, r_col = st.columns([7, 4], gap="large")
        with m_main_col:
            m_diet = st.radio("Switch Dietary Preference:", ["Vegetarian", "Non-Vegetarian"], horizontal=True, key="master_diet_pref")
            day_tabs = st.tabs(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"])
            for d_idx, day_name in enumerate(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]):
                with day_tabs[d_idx]:

                    st.markdown(f"### {day_name} Nutrition Schedule")
                    if d_idx < len(profile.weekly_meal_plan):
                        day_plan = profile.weekly_meal_plan[d_idx]
                    
                        day_items = day_plan.meal_plan
                        # Use the actual preference stored in session state
                        b_col = "#f0fdf4" if m_diet == "Vegetarian" else "#fff7ed"
                        bd_col = "#bbf7d0" if m_diet == "Vegetarian" else "#fed7aa"
                        t_col = "#166534" if m_diet == "Vegetarian" else "#ea580c"
                        st.markdown(f"<div style='background: {b_col}; padding: 18px; border-radius: 16px 16px 0 0; text-align: center; border: 1px solid {bd_col}; border-bottom: 4px solid {t_col};'><h4 style='margin: 0; color: {t_col}; font-weight: 800;'>{'🥦' if m_diet == 'Vegetarian' else '🍗'} {m_diet} Weekly Schedule</h4></div>", unsafe_allow_html=True)
                        m_tabs = st.tabs(["🌅 Breakfast", "☀️ Lunch", "🌙 Dinner", "🍿 Snacks"])
                        m_contents = [day_items.breakfast, day_items.lunch, day_items.dinner, day_items.snacks]
                        for m_idx, m_items in enumerate(m_contents):
                            with m_tabs[m_idx]:
                                bg_i = "#f0fdf4" if m_diet == "Vegetarian" else "#fff7ed"
                                br_i = "#bbf7d0" if m_diet == "Vegetarian" else "#fed7aa"
                                tx_i = "#166534" if m_diet == "Vegetarian" else "#9a3412"
                                for idx, m_item in enumerate(m_items):
                                    m_box_col1, m_box_col2 = st.columns([1, 1], gap="medium")
                                    with m_box_col1:
                                        # Compact meal box
                                        st.markdown(f'<div style="background-color: {bg_i}; border: 2px solid {br_i}; border-radius: 12px; padding: 14px; margin-bottom: 8px; display: flex; align-items: center; box-shadow: 0 4px 6px rgba(0,0,0,0.02); min-height: 70px;"><div style="background-color: {tx_i}; color: white; width: 28px; height: 28px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 14px; font-weight: 800; margin-right: 12px; flex-shrink: 0;">{idx+1}</div><div style="font-size: 18px; font-weight: 700; color: {tx_i}; line-height: 1.2;">{m_item.name if hasattr(m_item, "name") else m_item}</div></div>', unsafe_allow_html=True)
                                    
                                        # Integrated Log Button
                                        btn_key = f"log_{day_name}_{m_idx}_{idx}_{st.session_state.master_diet_pref}"
                                        if st.button("🍴 Log Intake", key=btn_key, use_container_width=True):
                                            st.session_state.consumed_log.append(m_item)
                                            st.toast(f"Logged: {m_item.name if hasattr(m_item, 'name') else m_item}!", icon="✅")
                                
                                    with m_box_col2:
                                        # Professional Interactive Chart Reveal
                                        if hasattr(m_item, "protein"):
                                            # Check if this specific item instance is in the log
                                            if m_item in st.session_state.consumed_log:
                                                render_nutrient_pie_chart(m_item, key=f"pie_{day_name}_{m_idx}_{idx}_{st.session_state.master_diet_pref}")
                                            else:
                                                render_chart_placeholder()
                                        else:
                                            st.info("Legacy/Simple item: No macros.")
                                    st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True)

                    else:
                        st.warning(f"🍱 AI Meal Plan for {day_name} was not fully generated. This occasionally happens with large reports—please try 'Get Recommendations' again to re-roll.")
                
                # Render Body Progress at the end of the day tab if anything is consumed
                if st.session_state.consumed_log:
                    st.divider()
                    st.markdown("### 📊 Your Collective Body Nutrition Status (Today)")
                    total_stats = {'calories': 0, 'protein': 0, 'carbs': 0, 'fats': 0, 'water': 0}
                    for item in st.session_state.consumed_log:
                        if hasattr(item, "calories"):
                            total_stats['calories'] += item.calories
                            total_stats['protein'] += item.protein
                            total_stats['carbs'] += item.carbs
                            total_stats['fats'] += item.fats
                            total_stats['water'] += item.water_ml
                    
                    p_col1, p_col2 = st.columns([1, 1], gap="large")
                    with p_col1:
                        if profile.daily_macros:
                            render_body_progress_chart(total_stats, profile.daily_macros, key=f"body_progress_{day_name}")
                    with p_col2:
                        # Extract numeric target from "3200 ml" or "3.2 L" string
                        try:
                            # Heuristic: Find digits in the hydration string
                            import re
                            target_ml = int(re.search(r'\d+', str(profile.hydration).replace('.','')).group())
                            if "L" in str(profile.hydration).upper() and "." in str(profile.hydration):
                                target_ml = int(float(re.search(r'[\d\.]+', str(profile.hydration)).group()) * 1000)
                            elif "L" in str(profile.hydration).upper():
                                target_ml = int(re.search(r'\d+', str(profile.hydration)).group()) * 1000
                        except:
                            target_ml = 3000 # Fallback
                            
                        water_pct = min(100, (total_stats['water']/target_ml)*100) if target_ml > 0 else 0
                        
                        st.markdown(f"""
                        <div style="background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%); padding: 30px; border-radius: 24px; border: 1px solid #e2e8f0; border-top: 8px solid #3b82f6; box-shadow: 0 15px 30px -10px rgba(59, 130, 246, 0.15);">
                            <div style="display: flex; justify-content: space-between; align-items: start;">
                                <div>
                                    <h4 style="margin: 0; color: #1e3a8a; font-weight: 900; font-size: 18px; text-transform: uppercase; letter-spacing: 1px;">💧 Hydration Status</h4>
                                    <p style="margin: 4px 0 0 0; color: #64748b; font-size: 14px; font-weight: 600;">Daily Target: {profile.hydration}</p>
                                </div>
                                <div style="background: #eff6ff; padding: 6px 12px; border-radius: 12px; color: #3b82f6; font-weight: 800; font-size: 13px; border: 1px solid #dbeafe;">
                                    {round(water_pct, 1)}% Complete
                                </div>
                            </div>
                            <div style="margin-top: 25px;">
                                <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                                    <span style="font-size: 32px; font-weight: 900; color: #0f172a;">{total_stats['water']}<small style="font-size: 16px; color: #64748b; margin-left: 4px;">ml</small></span>
                                    <span style="align-self: flex-end; color: #94a3b8; font-weight: 700; font-size: 14px;">{target_ml}ml Goal</span>
                                </div>
                                <div style="width: 100%; height: 16px; background: #f1f5f9; border-radius: 8px; overflow: hidden; border: 1px solid #e2e8f0;">
                                    <div style="width: {water_pct}%; height: 100%; background: linear-gradient(90deg, #3b82f6 0%, #60a5fa 100%); box-shadow: 0 0 15px rgba(59, 130, 246, 0.4); transition: width 1s cubic-bezier(0.34, 1.56, 0.64, 1);"></div>
                                </div>
                            </div>
                            <p style="margin-top: 15px; font-size: 12px; color: #94a3b8; font-style: italic; font-weight: 500;">Includes fluids tracked from food moisture & direct water logging.</p>
                        </div>
                        """, unsafe_allow_html=True)

        with r_col:
            st.markdown("<div style='background: #eff6ff; padding: 18px; border-radius: 16px 16px 0 0; text-align: center; border: 1px solid #bfdbfe; border-bottom: 4px solid #2563eb;'><h4 style='margin: 0; color: #1e40af; font-weight: 800;'>📍 Nearby Healthy Restaurants</h4></div><div style='padding: 1px;'>", unsafe_allow_html=True)
            if st.session_state.get('real_restaurants') or True:
                for res in st.session_state.get('real_restaurants', []):
                    r_rating = f"⭐ {res.get('rating')}" if res.get('rating') else ""
                    r_dist = res.get('distance_km')
                    r_dist_val = f" <span style='color:#ea580c;'>({r_dist} km away)</span>" if r_dist and r_dist != 999.9 else ""
                    st.markdown(f'<div style="background-color: #ffffff; border: 1px solid #e5e7eb; border-radius: 12px; padding: 18px; margin-bottom: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); transition: transform 0.2s;"><h4 style="margin: 0; color: #111827; font-weight: 800; font-size: 18px;">🍽️ {res.get("name")} {r_rating}</h4><p style="margin: 5px 0; color: #6b7280; font-size: 14px; font-weight: 600;">📍 {res.get("address")}{r_dist_val}</p><p style="margin: 5px 0 10px 0; color: #4b5563; font-style: italic; font-size: 14px;">"{res.get("snippet", "Top health choice")}"</p><a href="javascript:void(0);" style="display: block; width: 100%; padding: 8px 0; background-color: #f3f4f6; color: #4f46e5; font-weight: 700; text-align: center; text-decoration: none; border-radius: 8px; cursor: default;">View Full Menu ➔</a></div>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        styled_header("🛒 7. Automated Grocery Shopping List")
        g_cols = st.columns(len(profile.grocery_list) if profile.grocery_list else 1)
        for i, cat in enumerate(profile.grocery_list):
            with g_cols[i % len(g_cols)]:
                st.markdown(f'<div class="hover-card" style="margin-bottom: 20px;"><h4 style="color:#d97706; font-weight:800; border-bottom:2px solid #fde68a; padding-bottom:5px; margin-bottom:15px; text-transform:uppercase; font-size:14px;">{cat.category_name}</h4>', unsafe_allow_html=True)
                for item in cat.items:
                    st.markdown(f"<p style='color:#1f2937; font-size:14px; margin: 4px 0;'>• {item}</p>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
        
        styled_header("💧 8. Hydration Goal")
        st.markdown(f'<div style="text-align: center; padding: 30px; border-radius: 20px; background: #eff6ff; border: 1px solid #bfdbfe; width: 60%; margin: 0 auto; margin-bottom: 40px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);"><h2 style="margin:0; color:#1e3a8a; font-size: 38px; font-weight: 900;">{profile.hydration}</h2><p style="margin:0; color:#3b82f6; font-weight: 700; font-size: 14px; text-transform: uppercase; letter-spacing: 1px; margin-top: 5px;">Recommended Daily Target</p></div>', unsafe_allow_html=True)
        
        st.markdown("""
        <div style="text-align: center; padding: 60px 40px; border-radius: 24px; background: linear-gradient(135deg, #10b981 0%, #059669 100%); box-shadow: 0 10px 25px rgba(16, 185, 129, 0.3); margin-top: 40px; margin-bottom: 60px; position: relative; overflow: hidden;">
            <div style="font-size: 70px; margin-bottom: 15px; animation: bounceHero 3s infinite;">🏃‍♂️📈🥗</div>
            <h1 style="color: #ffffff; font-size: 50px; font-weight: 900; line-height: 1.1; margin-bottom: 25px; text-transform: uppercase; letter-spacing: 1px;">STAY CONSISTENT!</h1>
            <p style="color: #ffffff; font-size: 20px; line-height: 1.6; max-width: 800px; margin: 0 auto; font-weight: 500; opacity: 0.95;">
                Following this intelligently designed, personalized nutrient guide is your massive first step towards achieving total wellness. Remember, consistency is the ultimate key to unlocking the true life-changing benefits.
                <br><br><span style="color: #065f46; font-size: 24px; background: #ffffff; padding: 12px 30px; border-radius: 100px; display: inline-block; margin-top: 20px; font-weight: 800; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">You've absolutely got this! 🌟</span>
            </p>
            <style>@keyframes bounceHero { 0%, 20%, 50%, 80%, 100% {transform: translateY(0);} 40% {transform: translateY(-20px);} 60% {transform: translateY(-10px);} }</style>
        </div>
        """, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"An error occurred during rendering. Diagnostics: {e}")
