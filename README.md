# 🕵️‍♂️ AI-Powered Dark Web Search Tool

> An AI-powered OSINT tool that crawls the Dark Web based on your keyword and provides:
> - A list of active `.onion` links,
> - Live webpage previews (snippets),
> - And AI-generated contextual analysis of the page content.

---

## 🚀 Features

- 🔍 Keyword-based `.onion` link discovery
- ⚡ Highlights both **active** and **inactive** links
- 🤖 Integrated **AI explanation** per link
- 🖼️ Webpage preview/snippet functionality
- 🔐 Secure user login & account management
- 🧠 AI support via OpenAI (or compatible) API key

---

## 📦 Get Started

### 🔗 Git Clone

bash
git clone https://github.com/GargSaksham/AI-Powered-DarkWeb-Search.git
cd AI-Powered-DarkWeb-Search

### 🧱 Install Dependencies (via APT)

> No virtual environments — system-level installation using `apt`:

bash
sudo apt update
sudo apt install \
python3-pillow \
python3-bs4 \
python3-requests \
python3-flask \
python3-bcrypt \
python3-undetected-chromedriver \
python3-stem \
python3-flask-cors

### Install and Start tor

sudo apt install tor
sudo systemctl start tor

#### Check tor status
sudo systemctl status tor

###Run the Web Application

python3 app.py
Click on “Learn more and request demo”

### Account Creation and LogIn

Fill all fields — mandatory
Click Sign Up
Log in using your email and password

### Start Searching
Enter a keyword (e.g., drugs, malware, weapons)
Get a list of .onion links:
✅ Active links
❌ Inactive links

Copy any .onion link and open it in the Tor browser

Click on “View Details” to:

🖼️ See a preview/snippet of the .onion site

🤖 Read AI-powered analysis of its content

### Setup AI API Key

Required for the AI explanation feature.
OPENAI_API_KEY = "your-openai-key-here"

## Disclaimer
This tool is for educational and cybersecurity research purposes only.
The author does not support or condone any illegal activity.

### Contributions are Welcomed 
