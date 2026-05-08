import streamlit as st
import pandas as pd
import json
import os
import requests
import time
import re
import hashlib
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from bs4 import BeautifulSoup
from groq import Groq
import base64
import uuid
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

st.set_page_config(page_title="Astronomy AI", page_icon="🌌", layout="wide")

# ==========================================
# OWNER CONFIGURATION - FROM SECRETS (HIDDEN!)
# ==========================================
# For Hugging Face Secrets - add these:
# OWNER_EMAIL, ADMIN_PIN, GMAIL_EMAIL, GMAIL_APP_PASSWORD
try:
    OWNER_EMAIL = st.secrets.get("OWNER_EMAIL", "")
    ADMIN_PIN = st.secrets.get("ADMIN_PIN", "")
    GMAIL_EMAIL = st.secrets.get("GMAIL_EMAIL")
    GMAIL_APP_PASSWORD = st.secrets.get("GMAIL_APP_PASSWORD", "")
except:
    st.error("Secrets not configured properly")
    st.stop()

# ==========================================
# EMAIL SENDING FUNCTION
# ==========================================
def send_reset_email(to_email, reset_code):
    """Send password reset email via Gmail SMTP"""
    if not GMAIL_APP_PASSWORD:
        return False
    
    try:
        subject = "🔐 Password Reset - Astronomy AI"
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <h2 style="color: #4CAF50;">🌌 Astronomy AI - Password Reset</h2>
            <p>Hello,</p>
            <p>You requested a password reset for your Astronomy AI account.</p>
            <p style="font-size: 28px; font-weight: bold; background: #f0f0f0; padding: 15px; text-align: center; letter-spacing: 2px;">
                {reset_code}
            </p>
            <p>Enter this code in the app to reset your password.</p>
            <p>This code will expire in 1 hour.</p>
            <hr>
            <p style="color: #666; font-size: 12px;">If you didn't request this, please ignore this email.</p>
            <p style="color: #666; font-size: 12px;">- Astronomy AI Team</p>
        </body>
        </html>
        """
        
        msg = MIMEMultipart()
        msg["Subject"] = subject
        msg["From"] = GMAIL_EMAIL
        msg["To"] = to_email
        msg.attach(MIMEText(body, "html"))
        
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(GMAIL_EMAIL, GMAIL_APP_PASSWORD)
            server.send_message(msg)
        
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False

# ==========================================
# DISCLAIMER
# ==========================================
st.warning("""
⚠️ **PRIVACY NOTICE** ⚠️
This app is for educational purposes only.
- Do NOT share personal information
- Your chats are saved locally and only visible to you
**By using this app, you agree to these terms**
""")

# Custom CSS
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    section[data-testid="stSidebar"] {
        min-width: 280px;
        max-width: 320px;
        background-color: #0e1111;
        padding-top: 2rem;
    }
    
    section[data-testid="stSidebar"] + div {
        padding-left: 1rem;
    }
    
    .main > div {
        max-width: 800px;
        margin: 0 auto;
    }
    
    .stChatMessage {
        padding: 1rem;
        border-radius: 0.75rem;
        margin-bottom: 0.75rem;
    }
    
    .stButton button {
        border-radius: 8px;
        font-weight: 500;
    }
    
    .quick-prompt {
        background-color: #2b313e;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.8rem;
        cursor: pointer;
        margin: 0.2rem;
        display: inline-block;
    }
    .quick-prompt:hover {
        background-color: #3b4150;
    }
    
    .profile-pic {
        border-radius: 50%;
        object-fit: cover;
        margin-bottom: 10px;
    }
    
    .web-search-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        padding: 15px;
        border-radius: 12px;
        margin-bottom: 20px;
        border: 1px solid #2a3a5c;
    }
    
    .web-search-toggle-container {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 15px;
    }
    
    .web-search-label {
        font-size: 16px;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    .toggle-switch-large {
        position: relative;
        display: inline-block;
        width: 60px;
        height: 30px;
    }
    
    .toggle-switch-large input {
        opacity: 0;
        width: 0;
        height: 0;
    }
    
    .toggle-slider-large {
        position: absolute;
        cursor: pointer;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background-color: #ccc;
        border-radius: 34px;
        transition: 0.3s;
    }
    
    .toggle-slider-large:before {
        position: absolute;
        content: "";
        height: 24px;
        width: 24px;
        left: 3px;
        bottom: 3px;
        background-color: white;
        border-radius: 50%;
        transition: 0.3s;
    }
    
    input:checked + .toggle-slider-large {
        background-color: #4CAF50;
    }
    
    input:checked + .toggle-slider-large:before {
        transform: translateX(30px);
    }
    
    .web-search-status {
        font-size: 16px;
        font-weight: bold;
        padding: 5px 12px;
        border-radius: 20px;
    }
    
    .web-search-status.on {
        background-color: #4CAF50;
        color: white;
    }
    
    .web-search-status.off {
        background-color: #dc3545;
        color: white;
    }
    
    .quick-prompt-btn:active {
        pointer-events: none;
        opacity: 0.5;
    }
    
    .pro-card {
        background: linear-gradient(135deg, #2ecc71 0%, #27ae60 100%);
        padding: 15px;
        border-radius: 12px;
        margin: 10px 0;
        color: white;
    }
    
    .bmc-button {
        display: inline-block;
        background-color: #FFDD00;
        color: #000000;
        padding: 10px 20px;
        border-radius: 8px;
        text-decoration: none;
        font-weight: bold;
        margin: 5px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# SESSION STATE
# ==========================================
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_history_list" not in st.session_state:
    st.session_state.chat_history_list = []
if "current_chat_id" not in st.session_state:
    st.session_state.current_chat_id = datetime.now().strftime("%Y%m%d_%H%M%S")
if "username" not in st.session_state:
    st.session_state.username = None
if "user_email" not in st.session_state:
    st.session_state.user_email = None
if "user_avatar" not in st.session_state:
    st.session_state.user_avatar = None
if "deepthink_mode" not in st.session_state:
    st.session_state.deepthink_mode = False
if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = []
if "share_link" not in st.session_state:
    st.session_state.share_link = None
if "search_query" not in st.session_state:
    st.session_state.search_query = ""
if "editing_message" not in st.session_state:
    st.session_state.editing_message = None
if "temperature" not in st.session_state:
    st.session_state.temperature = 0.7
if "system_prompt" not in st.session_state:
    st.session_state.system_prompt = "You are a helpful astronomy assistant. Answer accurately and concisely about space."
if "pinned_chats" not in st.session_state:
    st.session_state.pinned_chats = []
if "language" not in st.session_state:
    st.session_state.language = "English"
if "web_search_in_chat" not in st.session_state:
    st.session_state.web_search_in_chat = False
if "last_click_time" not in st.session_state:
    st.session_state.last_click_time = 0
if "quick_prompt_disabled" not in st.session_state:
    st.session_state.quick_prompt_disabled = False
if "last_user_message" not in st.session_state:
    st.session_state.last_user_message = ""
if "is_pro" not in st.session_state:
    st.session_state.is_pro = False
if "daily_searches" not in st.session_state:
    st.session_state.daily_searches = 0
if "last_search_date" not in st.session_state:
    st.session_state.last_search_date = datetime.now().date().isoformat()
if "admin_authenticated" not in st.session_state:
    st.session_state.admin_authenticated = False
if "reset_requested" not in st.session_state:
    st.session_state.reset_requested = False
if "reset_token" not in st.session_state:
    st.session_state.reset_token = None
if "reset_email" not in st.session_state:
    st.session_state.reset_email = None

# Create necessary directories
os.makedirs("rate_limits", exist_ok=True)
os.makedirs("users", exist_ok=True)
os.makedirs("user_data", exist_ok=True)
os.makedirs("shared_chats", exist_ok=True)

# ==========================================
# USER AUTHENTICATION SYSTEM
# ==========================================
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def save_user(email, username, password_hash):
    users_file = "users/users.json"
    if os.path.exists(users_file):
        with open(users_file, "r") as f:
            users = json.load(f)
    else:
        users = {}
    
    users[email] = {
        "username": username,
        "password": password_hash,
        "created_at": datetime.now().isoformat(),
        "is_pro": False
    }
    
    with open(users_file, "w") as f:
        json.dump(users, f, indent=2)

def verify_user(email, password):
    users_file = "users/users.json"
    if not os.path.exists(users_file):
        return None
    
    with open(users_file, "r") as f:
        users = json.load(f)
    
    if email in users and users[email]["password"] == hash_password(password):
        return users[email]["username"]
    return None

def user_exists(email):
    users_file = "users/users.json"
    if not os.path.exists(users_file):
        return False
    with open(users_file, "r") as f:
        users = json.load(f)
    return email in users

def username_exists(username):
    users_file = "users/users.json"
    if not os.path.exists(users_file):
        return False
    with open(users_file, "r") as f:
        users = json.load(f)
    for user_data in users.values():
        if user_data["username"] == username:
            return True
    return False

def update_password(email, new_password):
    users_file = "users/users.json"
    if not os.path.exists(users_file):
        return False
    
    with open(users_file, "r") as f:
        users = json.load(f)
    
    if email in users:
        users[email]["password"] = hash_password(new_password)
        with open(users_file, "w") as f:
            json.dump(users, f, indent=2)
        return True
    return False

def is_owner():
    return st.session_state.get("user_email") == OWNER_EMAIL

# ==========================================
# PROFANITY FILTER
# ==========================================
BAD_WORDS = []

def contains_profanity(text):
    text_lower = text.lower()
    for word in BAD_WORDS:
        if word in text_lower:
            return True
    return False

def clean_prompt(prompt):
    for word in BAD_WORDS:
        prompt = re.sub(rf'\b{word}\b', '[filtered]', prompt, flags=re.IGNORECASE)
    return prompt

# ==========================================
# RATE LIMITING
# ==========================================
def check_rate_limit(username, max_per_hour=10):
    if st.session_state.is_pro:
        return True
    
    current_hour = datetime.now().replace(minute=0, second=0, microsecond=0)
    rate_file = f"rate_limits/{username}.json"
    
    if os.path.exists(rate_file):
        with open(rate_file, "r") as f:
            user_limits = json.load(f)
    else:
        user_limits = {"hour": current_hour.isoformat(), "count": 0}
    
    if datetime.fromisoformat(user_limits["hour"]) != current_hour:
        user_limits = {"hour": current_hour.isoformat(), "count": 0}
    
    if user_limits["count"] >= max_per_hour:
        return False
    
    user_limits["count"] += 1
    with open(rate_file, "w") as f:
        json.dump(user_limits, f)
    
    return True

# ==========================================
# TRANSLATIONS
# ==========================================
translations = {
    "English": {
        "title": "🌌 Astronomy AI",
        "ask": "Ask me about space...",
        "welcome": "Welcome back, {}!",
        "stats": "📊 NASA Database",
        "planets": "🪐 Planets",
        "stars": "⭐ Stars",
        "black_holes": "🕳️ Black Holes",
        "nebulae": "☁️ Nebulae",
        "new_chat": "➕ New Chat",
        "deepthink": "🧠 DeepThink Mode",
        "upload": "📁 Upload Files",
        "share": "🔗 Share Chat",
        "history": "📜 Chat History",
        "search": "🔍 Search conversations",
        "settings": "⚙️ Settings",
        "logout": "🚪 Logout",
        "web_search": "🌐 Web Search Mode"
    },
    "Urdu": {
        "title": "🌌 فلکیات اے آئی",
        "ask": "مجھ سے خلا کے بارے میں پوچھیں...",
        "welcome": "خوش آمدید، {}!",
        "stats": "📊 ناسا ڈیٹابیس",
        "planets": "🪐 سیارے",
        "stars": "⭐ ستارے",
        "black_holes": "🕳️ بلیک ہولز",
        "nebulae": "☁️ نیبیولا",
        "new_chat": "➕ نئی چیٹ",
        "deepthink": "🧠 گہری سوچ موڈ",
        "upload": "📁 فائلیں اپ لوڈ کریں",
        "share": "🔗 چیٹ شیئر کریں",
        "history": "📜 چیٹ ہسٹری",
        "search": "🔍 گفتگو تلاش کریں",
        "settings": "⚙️ ترتیبات",
        "logout": "🚪 لاگ آؤٹ",
        "web_search": "🌐 ویب سرچ موڈ"
    }
}

# ==========================================
# DATA LOADING
# ==========================================
@st.cache_data
def load_data():
    exoplanets = pd.read_csv('cleaned_exoplanets (1).csv')
    stars = pd.read_csv('nasa_stars_with_colors.csv')
    black_holes = pd.read_csv('black_holes.csv')
    nebulae = pd.read_csv('nebulae.csv')
    return exoplanets, stars, black_holes, nebulae

exoplanets, stars, black_holes, nebulae = load_data()

@st.cache_resource
def init_groq():
   return Groq(api_key=st.secrets.get("GROQ_API_KEY", ""))

client = init_groq()

@st.cache_data(ttl=86400)
def search_wikipedia(query):
    try:
        search_url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={query}&format=json"
        response = requests.get(search_url)
        data = response.json()
        if data['query']['search']:
            title = data['query']['search'][0]['title']
            summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{title.replace(' ', '_')}"
            summary_response = requests.get(summary_url)
            summary_data = summary_response.json()
            if 'extract' in summary_data:
                return {
                    "title": title,
                    "summary": summary_data['extract'][:500],
                    "url": f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}"
                }
    except:
        pass
    return None

# ==========================================
# CHAT FUNCTIONS
# ==========================================
def save_current_chat():
    if st.session_state.messages and st.session_state.username:
        user_dir = f"user_data/{st.session_state.username}"
        os.makedirs(user_dir, exist_ok=True)
        filename = f"{user_dir}/chat_{st.session_state.current_chat_id}.json"
        with open(filename, "w") as f:
            json.dump({
                "id": st.session_state.current_chat_id,
                "title": st.session_state.messages[0]["content"][:30] if st.session_state.messages else "New Chat",
                "messages": st.session_state.messages,
                "username": st.session_state.username,
                "user_avatar": st.session_state.user_avatar,
                "timestamp": datetime.now().isoformat(),
                "pinned": st.session_state.current_chat_id in st.session_state.pinned_chats
            }, f)
        load_chat_history_list()

def load_chat_history_list():
    st.session_state.chat_history_list = []
    if st.session_state.username:
        user_dir = f"user_data/{st.session_state.username}"
        if os.path.exists(user_dir):
            for file in os.listdir(user_dir):
                if file.endswith(".json"):
                    try:
                        with open(f"{user_dir}/{file}", "r") as f:
                            chat = json.load(f)
                            st.session_state.chat_history_list.append(chat)
                    except:
                        pass
            st.session_state.chat_history_list.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

def generate_share_link():
    if st.session_state.messages:
        chat_id = st.session_state.current_chat_id
        chat_data = {
            "id": chat_id,
            "messages": st.session_state.messages,
            "username": st.session_state.username,
            "user_avatar": st.session_state.user_avatar,
            "timestamp": datetime.now().isoformat()
        }
        shared_dir = "shared_chats"
        os.makedirs(shared_dir, exist_ok=True)
        with open(f"{shared_dir}/{chat_id}.json", "w") as f:
            json.dump(chat_data, f)
        share_url = f"https://huggingface.co/spaces/MZB17/astronomy-ai?chat_id={chat_id}"
        return share_url
    return None

def load_shared_chat(chat_id):
    try:
        with open(f"shared_chats/{chat_id}.json", "r") as f:
            return json.load(f)
    except:
        return None

def generate_pdf():
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    
    for msg in st.session_state.messages:
        story.append(Paragraph(f"<b>{msg['role'].upper()}:</b> {msg['content']}", styles['Normal']))
        story.append(Spacer(1, 12))
    
    doc.build(story)
    return buffer.getvalue()

# ==========================================
# WEB SEARCH
# ==========================================
def web_search(query):
    try:
        url = f"https://html.duckduckgo.com/html/?q={query}"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        results = soup.select('.result')
        
        search_results = []
        for result in results[:5]:
            title_elem = result.select_one('.result__a')
            snippet_elem = result.select_one('.result__snippet')
            if title_elem:
                title = title_elem.text
                link = title_elem.get('href', '')
                snippet = snippet_elem.text if snippet_elem else ""
                search_results.append({"title": title, "link": link, "snippet": snippet})
        return search_results
    except Exception as e:
        return []

# ==========================================
# RESPONSE GENERATION
# ==========================================
def generate_response(prompt, use_deepthink=False, use_web_search=False):
    
    if use_web_search and not check_rate_limit(st.session_state.username):
        return "🔒 **Rate limit reached!** You've used 10 web searches this hour.\n\nPlease try again later or upgrade to Pro for unlimited!", None, None
    
    if contains_profanity(prompt):
        st.warning("⚠️ Please use appropriate language.")
        prompt = clean_prompt(prompt)
    
    today = datetime.now().date().isoformat()
    if st.session_state.last_search_date != today:
        st.session_state.daily_searches = 0
        st.session_state.last_search_date = today
    
    if use_web_search and not st.session_state.is_pro:
        if st.session_state.daily_searches >= 10:
            return "🔒 **Free limit reached!** You've used 10 web searches today.\n\n✨ **Support on Buy Me a Coffee to unlock Pro!**", None, None
        st.session_state.daily_searches += 1
        remaining = 10 - st.session_state.daily_searches
        st.info(f"📊 Free tier: {remaining} searches left today")
    
    if prompt == st.session_state.last_user_message:
        return "⚠️ You just asked that! Try a different question.", None, None
    
    st.session_state.last_user_message = prompt
    
    q = prompt.lower()
    table_data = None
    
    if use_web_search:
        web_results = web_search(prompt)
        if web_results:
            context = "🌐 Web search results:\n"
            for r in web_results[:3]:
                context += f"- {r['title']}: {r['snippet']}\n"
            prompt = f"{context}\n\nUser asked: {prompt}\n\nAnswer based on the above search results."
    
    if "exoplanet" in q or "planet" in q:
        results = exoplanets[exoplanets['pl_name'].str.contains(prompt, case=False, na=False)]
        if len(results) > 0:
            return f"🪐 **EXOPLANET SEARCH**\n\nFound **{len(results)}** planet(s):", results[['pl_name', 'pl_rade']].head(5), None
    
    elif "star" in q:
        results = stars[stars['name'].str.contains(prompt, case=False, na=False)]
        if len(results) > 0:
            return f"⭐ **STAR SEARCH**\n\nFound **{len(results)}** star(s):", results[['name', 'temperature', 'color']].head(5), None
    
    elif "black hole" in q:
        results = black_holes[black_holes['name'].str.contains(prompt, case=False, na=False)]
        if len(results) > 0:
            return f"🕳️ **BLACK HOLE SEARCH**\n\nFound **{len(results)}** black hole(s):", results[['name', 'type', 'location']].head(5), None
    
    elif "nebula" in q:
        results = nebulae[nebulae['name'].str.contains(prompt, case=False, na=False)]
        if len(results) > 0:
            return f"☁️ **NEBULA SEARCH**\n\nFound **{len(results)}** nebula(e):", results[['name', 'type', 'location']].head(5), None
    
    wiki_result = search_wikipedia(prompt)
    if wiki_result:
        return f"📖 **WIKIPEDIA**\n\n{wiki_result['summary']}", None, wiki_result
    
    try:
        system_prompt = st.session_state.system_prompt
        
        if use_deepthink:
            system_prompt += " Provide detailed, step-by-step explanation."
        else:
            system_prompt += " Provide concise, direct answers."
        
        if st.session_state.uploaded_files:
            system_prompt += f"\n\nUser uploaded {len(st.session_state.uploaded_files)} file(s)."
        
        messages = [{"role": "system", "content": system_prompt}]
        for msg in st.session_state.messages[-15:]:
            messages.append({"role": msg["role"], "content": msg["content"]})
        messages.append({"role": "user", "content": prompt})
        
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=st.session_state.temperature,
            max_tokens=500
        )
        raw_response = completion.choices[0].message.content
        
        formatted_lines = []
        lines = raw_response.split('\n')
        
        for line in lines:
            if line.strip():
                if line.strip().endswith('?'):
                    formatted_lines.append(f"**🔍 {line.strip()}**")
                elif line.strip().startswith(('-', '•', '*', '1.', '2.', '3.')):
                    cleaned = line.strip().lstrip('-•*0123456789. ')
                    formatted_lines.append(f"  • {cleaned}")
                else:
                    formatted_lines.append(f"{line.strip()}")
        
        final_response = "\n\n".join(formatted_lines)
        
        if use_deepthink:
            final_response = "🧠 **DeepThink Mode**\n\n" + final_response
        if use_web_search:
            final_response = "🌐 **Web Search Mode**\n\n" + final_response
        
        return f"🦙 **ASTRONOMY AI**\n\n{final_response}", None, None
    except Exception as e:
        return f"❌ Error: {str(e)}", None, None

# ==========================================
# SHARED CHAT LOADING
# ==========================================
query_params = st.query_params
if "chat_id" in query_params:
    shared_chat = load_shared_chat(query_params["chat_id"])
    if shared_chat:
        st.session_state.messages = shared_chat["messages"]
        st.session_state.username = shared_chat["username"]
        st.session_state.user_avatar = shared_chat.get("user_avatar")
        st.session_state.current_chat_id = shared_chat["id"]

# ==========================================
# LOGIN/SIGNUP SYSTEM WITH REAL EMAIL RESET (FIXED)
# ==========================================
if st.session_state.username is None:
    st.title("🌌 Welcome to Astronomy AI")
    st.markdown("### Sign in to continue")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.image("https://cdn-icons-png.flaticon.com/512/1999/1999625.png", width=100)
    with col2:
        tab1, tab2, tab3 = st.tabs(["🔐 Login", "📝 Sign Up", "🔄 Forgot Password"])
        
        # ========== LOGIN TAB ==========
        with tab1:
            login_email = st.text_input("Email", placeholder="you@example.com", key="login_email")
            login_password = st.text_input("Password", type="password", key="login_password")
            
            if st.button("Login", use_container_width=True, key="login_btn"):
                if login_email and login_password:
                    username = verify_user(login_email, login_password)
                    if username:
                        st.session_state.username = username
                        st.session_state.user_email = login_email
                        load_chat_history_list()
                        if st.session_state.chat_history_list:
                            last_chat = st.session_state.chat_history_list[0]
                            st.session_state.messages = last_chat["messages"]
                            st.session_state.user_avatar = last_chat.get("user_avatar")
                            st.session_state.current_chat_id = last_chat["id"]
                        st.rerun()
                    else:
                        st.error("Invalid email or password")
                else:
                    st.warning("Please enter email and password")
        
        # ========== SIGN UP TAB ==========
        with tab2:
            signup_email = st.text_input("Email", placeholder="you@example.com", key="signup_email")
            signup_username = st.text_input("Username", placeholder="Your username", key="signup_username")
            signup_password = st.text_input("Password", type="password", key="signup_password")
            signup_confirm = st.text_input("Confirm Password", type="password", key="signup_confirm")
            uploaded_avatar = st.file_uploader("Profile picture (optional)", type=["png", "jpg", "jpeg"], key="signup_avatar")
            
            if st.button("Create Account", use_container_width=True, key="signup_btn"):
                if not signup_email or not signup_username or not signup_password:
                    st.warning("Please fill all fields")
                elif signup_password != signup_confirm:
                    st.warning("Passwords do not match")
                elif len(signup_password) < 6:
                    st.warning("Password must be at least 6 characters")
                elif len(signup_username) < 2:
                    st.warning("Username must be at least 2 characters")
                elif len(signup_username) > 20:
                    st.warning("Username must be less than 20 characters")
                elif contains_profanity(signup_username):
                    st.warning("Please choose a different username")
                elif user_exists(signup_email):
                    st.error("Email already registered")
                elif username_exists(signup_username):
                    st.error("Username already taken")
                else:
                    avatar_base64 = None
                    if uploaded_avatar:
                        avatar_base64 = base64.b64encode(uploaded_avatar.read()).decode()
                    
                    save_user(signup_email, signup_username, hash_password(signup_password))
                    
                    st.session_state.username = signup_username
                    st.session_state.user_email = signup_email
                    st.session_state.user_avatar = avatar_base64
                    st.success("Account created! Welcome!")
                    st.rerun()
        
        # ========== FORGOT PASSWORD TAB (FIXED - removed duplicate if) ==========
        with tab3:
            st.markdown("### Reset Your Password")
            st.info("Enter your email address and we'll send you a reset code.")
            
            reset_email_input = st.text_input("Email", placeholder="you@example.com", key="reset_email_input")
            
            if st.button("Send Reset Code", use_container_width=True, key="reset_btn"):
                if reset_email_input and user_exists(reset_email_input):
                    reset_token = secrets.token_hex(8)
                    st.session_state.reset_token = reset_token
                    st.session_state.reset_email = reset_email_input
                    st.session_state.reset_requested = True
                    
                    # SEND REAL EMAIL
                    if send_reset_email(reset_email_input, reset_token):
                        st.success(f"✅ Reset code sent to {reset_email_input}! Check your email inbox.")
                        st.info("📧 The email may take 10-30 seconds to arrive. Check your spam folder if not found.")
                    else:
                        st.error("Failed to send email. Please make sure Gmail is configured properly.")
                elif reset_email_input:
                    st.error("Email not found. Please sign up first.")
                else:
                    st.warning("Please enter your email")
            
            # Show reset form if requested
            if st.session_state.get("reset_requested", False):
                st.markdown("---")
                st.markdown("### Enter New Password")
                
                new_password = st.text_input("New Password", type="password", key="new_password")
                confirm_password = st.text_input("Confirm New Password", type="password", key="confirm_password")
                entered_token = st.text_input("Reset Code", placeholder="Enter the code sent to your email", key="entered_token")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Reset Password", use_container_width=True, key="reset_password_btn"):
                        if entered_token == st.session_state.reset_token:
                            if new_password and confirm_password:
                                if new_password == confirm_password:
                                    if len(new_password) >= 6:
                                        if update_password(st.session_state.reset_email, new_password):
                                            st.success("✅ Password reset successfully! Please login with your new password.")
                                            st.balloons()
                                            st.session_state.reset_requested = False
                                            st.session_state.reset_token = None
                                            st.session_state.reset_email = None
                                        else:
                                            st.error("Failed to reset password")
                                    else:
                                        st.warning("Password must be at least 6 characters")
                                else:
                                    st.warning("Passwords do not match")
                            else:
                                st.warning("Please enter a new password")
                        else:
                            st.error("Invalid reset code. Please check your email and try again.")
                with col2:
                    if st.button("Cancel", key="cancel_reset_btn"):
                        st.session_state.reset_requested = False
                        st.session_state.reset_token = None
                        st.rerun()
    st.stop()

# ==========================================
# AFTER LOGIN
# ==========================================
load_chat_history_list()

# ==========================================
# SIDEBAR
# ==========================================
t = translations[st.session_state.language]
with st.sidebar:
    st.markdown(f"### {t['title']}")
    
    if st.session_state.user_avatar:
        st.image(f"data:image/png;base64,{st.session_state.user_avatar}", width=80, caption=f"@{st.session_state.username}")
    else:
        st.markdown(f"*Welcome, {st.session_state.username}*")
    st.caption(f"📧 {st.session_state.user_email}")
    st.markdown("---")
    
    with st.popover("⚙️ Settings"):
        st.markdown("### Account Settings")
        new_avatar = st.file_uploader("Update profile picture", type=["png", "jpg", "jpeg"], key="avatar_upload")
        if new_avatar:
            st.session_state.user_avatar = base64.b64encode(new_avatar.read()).decode()
            st.rerun()
        
        st.session_state.language = st.selectbox("🌐 Language", ["English", "Urdu"])
        st.session_state.temperature = st.slider("🎛️ Creativity", 0.0, 1.5, st.session_state.temperature, 0.05)
        st.session_state.system_prompt = st.text_area("🤖 System Prompt", st.session_state.system_prompt, height=100)
        
        st.markdown("---")
        if st.button("📋 Copy User ID", key="copy_id_btn"):
            st.success("Copied!")
        
        if st.button("📄 Export Chat as PDF", key="export_pdf_btn"):
            if st.session_state.is_pro or len(st.session_state.messages) < 20:
                pdf_data = generate_pdf()
                st.download_button("Download PDF", pdf_data, file_name=f"chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf", key="download_pdf_btn")
            else:
                st.warning("Free users can export up to 20 messages. Upgrade to Pro for unlimited!")
    
    st.markdown("---")
    
    st.markdown("### 🔄 Account")
    if st.button("🚪 Logout", use_container_width=True, key="logout_btn"):
        st.session_state.username = None
        st.session_state.user_email = None
        st.session_state.user_avatar = None
        st.session_state.messages = []
        st.rerun()
    
    st.markdown("---")
    
    # ==========================================
    # ADMIN PANEL - ONLY VISIBLE TO OWNER
    # ==========================================
    if is_owner():
        with st.expander("🔐 Admin Access"):
            pin_input = st.text_input("Enter Admin PIN:", type="password", key="admin_pin")
            if st.button("Verify Admin", key="verify_admin_btn"):
                if pin_input == ADMIN_PIN:
                    st.session_state.admin_authenticated = True
                    st.success("Admin access granted!")
                    st.rerun()
                else:
                    st.error("Wrong PIN")
        
        if st.session_state.get("admin_authenticated", False):
            st.markdown("### 📊 Admin Dashboard")
            total_users = len([d for d in os.listdir("user_data") if os.path.isdir(os.path.join("user_data", d))]) if os.path.exists("user_data") else 0
            st.metric("Total Users", total_users)
            
            total_chats = 0
            if os.path.exists("user_data"):
                for user in os.listdir("user_data"):
                    user_path = os.path.join("user_data", user)
                    if os.path.isdir(user_path):
                        total_chats += len([f for f in os.listdir(user_path) if f.endswith(".json")])
            st.metric("Total Chats", total_chats)
            st.info("🔒 Admin features coming soon")
        
        st.markdown("---")
    
    st.markdown("### 🚨 Report Issue")
    with st.expander("Report a problem", expanded=False):
        report_type = st.selectbox("Issue type", ["Bug", "Inappropriate response", "Technical issue", "Other"], key="report_type")
        report_description = st.text_area("Describe the issue:", key="report_desc")
        if st.button("📧 Send Report", key="send_report_btn"):
            if report_description:
                subject = f"Astronomy AI Report - {report_type}"
                body = f"Report from: {st.session_state.username} ({st.session_state.user_email})\n\nType: {report_type}\n\n{report_description}"
                mailto_link = f"mailto:astronomyai@gmail.com?subject={subject}&body={body}"
                st.markdown(f'<a href="{mailto_link}" target="_blank"><button style="background:#FF0000; color:white; padding:10px; border:none; border-radius:8px;">📧 Open Email</button></a>', unsafe_allow_html=True)
                st.info("Click button to send report")
            else:
                st.warning("Please describe the issue")
    
    st.markdown("---")
    
    st.markdown("### ☕ Support the Creator")
    st.markdown("""
    <div style="text-align: center; background: linear-gradient(135deg, #FFDD00 0%, #FFC700 100%); padding: 15px; border-radius: 12px; margin: 10px 0;">
        <h4 style="color: #000;">🚀 Buy Me a Coffee</h4>
        <p style="color: #000;">Get UNLIMITED web searches & PDF exports!</p>
        <a href="https://www.buymeacoffee.com/zain768007z" target="_blank" style="background: #000; color: #FFDD00; padding: 10px 20px; border-radius: 8px; text-decoration: none; display: inline-block;">
            ☕ Support for $3 (Rs. 500)
        </a>
        <p style="color: #000; font-size: 12px; margin-top: 10px;">Email: astronomyai@gmail.com</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("✨ I've Supported - Unlock Pro ✨", key="unlock_pro_btn"):
        st.session_state.is_pro = True
        st.success("🎉 Pro Unlocked! Thank you!")
        st.balloons()
        st.rerun()
    
    st.caption("Support a Gen Alpha Pakistani dev! 🇵🇰")
    st.markdown("---")
    
    if st.session_state.is_pro:
        st.success("🎉 **PRO ACTIVE** 🎉")
    else:
        st.info(f"📊 Today: {st.session_state.daily_searches}/10 free searches")
        st.warning("💡 Buy Me a Coffee to remove limits!")
    
    st.markdown("---")
    
    st.markdown("### 🌐 Web Search")
    web_search_query = st.text_input("Search the internet:", placeholder="Search Google...", key="web_search_input")
    if st.button("🔍 Search Web", use_container_width=True, key="web_search_btn"):
        if web_search_query:
            with st.spinner("🦙 Searching..."):
                results = web_search(web_search_query)
                if results:
                    for result in results:
                        st.markdown(f"**{result['title']}**")
                        st.markdown(f"[Link]({result['link']})")
                        st.caption(result['snippet'])
                        st.markdown("---")
                else:
                    st.info("No results found.")
        else:
            st.warning("Enter a search term")
    
    st.markdown("---")
    
    if st.button(t['new_chat'], use_container_width=True, key="new_chat_btn"):
        save_current_chat()
        st.session_state.messages = []
        st.session_state.current_chat_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        st.rerun()
    
    st.markdown("---")
    st.session_state.deepthink_mode = st.toggle(t['deepthink'], value=st.session_state.deepthink_mode, key="deepthink_toggle")
    
    st.markdown("---")
    
    st.markdown(f"### {t['upload']}")
    with st.expander("Click to upload files", expanded=False):
        uploaded_file = st.file_uploader("Choose a file", type=["csv", "txt", "json", "pdf", "md", "png", "jpg", "jpeg"], key="file_uploader")
        if uploaded_file is not None:
            try:
                file_content = uploaded_file.read()
                if len(file_content) > 5000000 and not st.session_state.is_pro:
                    st.error("File too large! Free users limited to 5MB. Upgrade to Pro for larger files!")
                else:
                    st.session_state.uploaded_files.append({
                        "name": uploaded_file.name,
                        "size": len(file_content),
                        "type": uploaded_file.type,
                        "timestamp": datetime.now().isoformat()
                    })
                    st.success(f"✅ Added {uploaded_file.name}")
            except Exception as e:
                st.error(f"Error: {e}")
    
    if st.session_state.uploaded_files:
        st.markdown("**📄 Your Files:**")
        for idx, f in enumerate(st.session_state.uploaded_files[-5:]):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.caption(f"📄 {f['name']}")
            with col2:
                if st.button("❌", key=f"del_file_{idx}"):
                    st.session_state.uploaded_files.remove(f)
                    st.rerun()
    
    st.markdown("---")
    
    st.markdown(f"### {t['share']}")
    share_url = generate_share_link()
    if share_url:
        whatsapp_msg = f"Check out my space chat!\n{share_url}"
        gmail_subject = "My Astronomy AI Chat"
        gmail_body = f"I had this conversation about space:\n{share_url}"
        twitter_msg = f"Just had this space chat with Astronomy AI! {share_url}"
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f'<a href="https://wa.me/?text={whatsapp_msg}" target="_blank"><button style="background:#25D366; color:white; padding:0.5rem; border:none; border-radius:8px; width:100%;">📱 WhatsApp</button></a>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'<a href="mailto:?subject={gmail_subject}&body={gmail_body}" target="_blank"><button style="background:#D44638; color:white; padding:0.5rem; border:none; border-radius:8px; width:100%;">📧 Gmail</button></a>', unsafe_allow_html=True)
        with col3:
            st.markdown(f'<a href="https://twitter.com/intent/tweet?text={twitter_msg}" target="_blank"><button style="background:#1DA1F2; color:white; padding:0.5rem; border:none; border-radius:8px; width:100%;">🐦 Twitter</button></a>', unsafe_allow_html=True)
    else:
        st.info("Start a conversation to share")
    
    st.markdown("---")
    
    st.markdown(f"### {t['stats']}")
    
    with st.expander(f"🪐 Planets ({len(exoplanets)})"):
        st.dataframe(exoplanets[['pl_name', 'pl_rade']].head(10))
        if st.button("🔍 Ask about exoplanets", key="ask_planets_btn"):
            st.session_state.messages.append({"role": "user", "content": "Tell me about exoplanets"})
            st.rerun()
        if st.button("📊 Show random planet", key="random_planet_btn"):
            random_planet = exoplanets.sample(1).iloc[0]
            st.session_state.messages.append({"role": "user", "content": f"Tell me about {random_planet['pl_name']}"})
            st.rerun()
    
    with st.expander(f"⭐ Stars ({len(stars)})"):
        st.dataframe(stars[['name', 'temperature', 'color']].head(10))
        if st.button("🔍 Ask about stars", key="ask_stars_btn"):
            st.session_state.messages.append({"role": "user", "content": "Tell me about stars"})
            st.rerun()
    
    with st.expander(f"🕳️ Black Holes ({len(black_holes)})"):
        st.dataframe(black_holes[['name', 'type', 'location']].head(10))
        if st.button("🔍 Ask about black holes", key="ask_bh_btn"):
            st.session_state.messages.append({"role": "user", "content": "Tell me about black holes"})
            st.rerun()
    
    with st.expander(f"☁️ Nebulae ({len(nebulae)})"):
        st.dataframe(nebulae[['name', 'type', 'location']].head(10))
        if st.button("🔍 Ask about nebulae", key="ask_neb_btn"):
            st.session_state.messages.append({"role": "user", "content": "Tell me about nebulae"})
            st.rerun()
    
    st.markdown("---")
    
    st.markdown(f"### {t['history']}")
    for idx, chat in enumerate(st.session_state.chat_history_list[:20]):
        if st.button(f"💬 {chat['title'][:25]}...", key=f"chat_history_{idx}"):
            save_current_chat()
            st.session_state.messages = chat['messages']
            st.session_state.current_chat_id = chat['id']
            st.session_state.user_avatar = chat.get("user_avatar")
            st.rerun()
    
    st.markdown("---")
    
    st.markdown(f"**{st.session_state.username}**")
    st.caption("👑 Gen Alpha | Pakistan | Powered by Groq Llama 3")

# ==========================================
# MAIN CHAT
# ==========================================

st.title(t['title'])
st.caption(t['welcome'].format(st.session_state.username))

MAX_CHARS = 3000

col_web1, col_web2 = st.columns([2, 1])
with col_web1:
    web_toggle = st.toggle(
        "🌐 Web Search Mode", 
        value=st.session_state.web_search_in_chat,
        help="When ON, the AI will search the internet",
        key="web_toggle_main"
    )
    if web_toggle != st.session_state.web_search_in_chat:
        st.session_state.web_search_in_chat = web_toggle
        st.rerun()
with col_web2:
    if st.session_state.web_search_in_chat:
        st.markdown("### 🟢 ACTIVE")
    else:
        st.markdown("### ⚪ OFF")

if st.session_state.web_search_in_chat:
    if st.session_state.is_pro:
        st.info("🌐 Web search ACTIVE (Pro: Unlimited)")
    else:
        st.info(f"🌐 Web search ACTIVE ({10 - st.session_state.daily_searches} searches left)")
else:
    st.caption("💡 Toggle ON for live web search")

st.markdown("---")

st.markdown("### 🔥 Quick Prompts")
quick_cols = st.columns(4)
quick_prompts = [
    "Explain black holes simply",
    "Compare Earth vs Mars",
    "What is a supernova?",
    "Can humans live on Jupiter?"
]

def send_quick_prompt(prompt_text):
    st.session_state.messages.append({"role": "user", "content": prompt_text})
    with st.chat_message("user"):
        st.markdown(prompt_text)
    with st.chat_message("assistant"):
        with st.spinner("🦙 Analyzing space data..."):
            response, table_data, wiki_data = generate_response(
                prompt_text, 
                st.session_state.deepthink_mode,
                st.session_state.web_search_in_chat
            )
            st.markdown(response)
            if table_data is not None:
                st.dataframe(table_data)
            if wiki_data:
                with st.expander("📖 Wikipedia Source"):
                    st.markdown(f"**{wiki_data['title']}**")
                    st.markdown(f"[Read more]({wiki_data['url']})")
    st.session_state.messages.append({
        "role": "assistant",
        "content": response,
        "table": table_data if table_data is not None else None,
        "wikipedia": wiki_data if wiki_data is not None else None
    })
    save_current_chat()

for i, prompt_text in enumerate(quick_prompts):
    with quick_cols[i]:
        if st.button(prompt_text, key=f"quick_prompt_{i}", use_container_width=True):
            send_quick_prompt(prompt_text)
            st.rerun()

st.markdown("---")

for i, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        if msg["role"] == "user":
            col1, col2 = st.columns([6, 1])
            with col2:
                if st.button("✏️", key=f"edit_msg_{i}"):
                    st.session_state.editing_message = i
            
            if st.session_state.editing_message == i:
                new_content = st.text_area("Edit message", msg["content"], key=f"edit_area_{i}")
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.button("Save", key=f"save_edit_{i}"):
                        st.session_state.messages[i]["content"] = new_content
                        st.session_state.editing_message = None
                        st.rerun()
                with col_btn2:
                    if st.button("Cancel", key=f"cancel_edit_{i}"):
                        st.session_state.editing_message = None
                        st.rerun()
            else:
                st.markdown(msg["content"])
        else:
            st.markdown(msg["content"])
            col1, col2 = st.columns([6, 1])
            with col2:
                if st.button("📋 Copy", key=f"copy_msg_{i}"):
                    st.toast("Copied!", icon="✅")
        
        if "table" in msg and msg["table"] is not None:
            st.dataframe(msg["table"])
        if "wikipedia" in msg and msg["wikipedia"] is not None:
            with st.expander("📖 Wikipedia Source"):
                st.markdown(f"**{msg['wikipedia']['title']}**")
                st.markdown(f"[Read more]({msg['wikipedia']['url']})")

prompt = st.chat_input(t['ask'] + (" (web search active)" if st.session_state.web_search_in_chat else ""))

if prompt:
    if len(prompt) > MAX_CHARS:
        st.error(f"⚠️ Message too long! Max {MAX_CHARS} characters.")
        st.stop()
    
    if contains_profanity(prompt):
        st.warning("⚠️ Please use appropriate language.")
        prompt = clean_prompt(prompt)
    
    st.session_state.last_user_message = ""
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        with st.spinner("🦙 Llama 3 thinking..."):
            response, table_data, wiki_data = generate_response(
                prompt, 
                st.session_state.deepthink_mode,
                st.session_state.web_search_in_chat
            )
            st.markdown(response)
            if table_data is not None:
                st.dataframe(table_data)
            if wiki_data:
                with st.expander("📖 Wikipedia Source"):
                    st.markdown(f"**{wiki_data['title']}**")
                    st.markdown(f"[Read more]({wiki_data['url']})")
    
    st.session_state.messages.append({
        "role": "assistant",
        "content": response,
        "table": table_data if table_data is not None else None,
        "wikipedia": wiki_data if wiki_data is not None else None
    })
    
    save_current_chat()
    st.rerun()

st.markdown("---")
st.caption("Powered by Groq Llama 3 | NASA Exoplanet Archive | Wikipedia | Web Search | Share any chat with a link! | Edit messages | Copy responses | Multi-language | PDF Export | Clickable NASA Database | Real DeepThink Mode | Profile Pictures")
