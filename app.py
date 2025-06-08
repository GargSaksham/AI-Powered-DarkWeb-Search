#from flask import Flask, request, jsonify
import requests
from flask import Flask, request, jsonify, send_from_directory
import threading
from stem.control import Controller
from stem import Signal
from bs4 import BeautifulSoup
from flask_cors import CORS
import time
import logging
import sqlite3
from concurrent.futures import ThreadPoolExecutor, as_completed
import bcrypt
import os
from word_recommendations import recommendation_system
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
#from webdriver_manager.chrome import ChromeDriverManager
import base64
from io import BytesIO
from PIL import Image
from link_details import LinkDetailsManager
import random

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('darkweb_search.log')
    ]
)

app = Flask(__name__,static_folder='static')
#app = Flask(__name__, static_folder='static', template_folder='static')
CORS(app)  # Enable CORS for all routes



DB_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = "/tmp/userDB.sqlite"
print(f"Database path: {DB_PATH}")

# Connect to SQLite database
try:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    cursor = conn.cursor()

    # Create table if not exists
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phonenumber TEXT NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()
except Exception as e:
    print(f"Error connecting to SQLite: {e}")
    # Ensure the directory exists
    os.makedirs(DB_DIR, exist_ok=True)
    # Try to connect again
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    cursor = conn.cursor()

# Configuration
TOR_PROXY = {
    "http": "socks5h://127.0.0.1:9050", 
    "https": "socks5h://127.0.0.1:9050"
}

# Search rate limiting
SEARCH_COOLDOWN = 5  # seconds between searches
last_search_time = {}  # Store last search time per IP
MAX_CONSECUTIVE_FAILURES = 3  # Max failures before rotating circuit

# Track failed engines
engine_failures = {}
failed_engines = set()

ONION_SEARCH_ENGINES = {
    "Torgle": "http://iy3544gmoeclh5de6gez2256v6pjh4omhpqdh2wpeeppjtvqmjhkfwad.onion/torgle/?query=",
    "Omega": "http://xmh57jrknzkhv6y3ls3ubitzfqnkrwxhopf5aygthi7d6rplyvk3noyd.onion/cgi-bin/omega/omega?P=",
    "torch": "http://torchdeedp3i2jigzjdmfpn5ttjhthh5wbmda2rr3jvqjg5p77c54dqd.onion/search?query=",
    "Oni": "http://freshonifyfe4rmuh6qwpsexfhdrww7wnt5qmkoertwxmcuvm4woo4ad.onion/?query=",
    "oss": "http://3fzh7yuupdfyjhwt3ugzqqof6ulbcl27ecev33knxe3u7goi3vfn2qqd.onion/oss/index.php?search=",
    "onn": "http://3bbad7fauom4d6sgppalyqddsqbf5u5p56b5k5uk2zxsy3d6ey2jobad.onion/search?q=",
    "krak": "http://krakenai2gmgwwqyo7bcklv2lzcvhe7cxzzva2xpygyax5f33oqnxpad.onion/search/?q=",
    "onn1": "http://2fd6cemt4gmccflhm6imvdfvli3nf7zn6rfrwpsy7uhxrgbypvwf5fad.onion/search?query=",
    "duck": "https://duckduckgogg42xjoc72x3sjasowoarfbgcmvfimaftt6twagswzczad.onion/?q=",
    "dane": "http://danexio627wiswvlpt6ejyhpxl5gla5nt2tgvgm2apj2ofrgm44vbeyd.onion/search?q="
}

TOR_CONTROL_PORT = 9051
TOR_PASSWORD = 'your_password'  # Change to your Tor control password

# Initialize LinkDetailsManager
link_details_manager = LinkDetailsManager(TOR_PROXY)

@app.before_request
def log_request_info():
    logging.info(f"Incoming request: {request.method} {request.url}")

def should_rotate_circuit():
    """Check if we need to rotate the Tor circuit"""
    return len(failed_engines) >= MAX_CONSECUTIVE_FAILURES

def reset_engine_status():
    """Reset the status of failed engines after circuit rotation"""
    failed_engines.clear()
    engine_failures.clear()

def change_identity():
    """Change Tor circuit to get a new IP"""
    try:
        with Controller.from_port(port=TOR_CONTROL_PORT) as controller:
            controller.authenticate(password=TOR_PASSWORD)
            controller.signal(Signal.NEWNYM)
            time.sleep(5)  # Wait for new circuit
            logging.info("Successfully changed Tor identity")
            reset_engine_status()  # Reset failed engines after rotation
            return True
    except Exception as e:
        logging.error(f"Failed to change Tor identity: {str(e)}")
        return False

def check_rate_limit(ip_address):
    """Check if we should allow another search based on rate limiting"""
    current_time = datetime.now()
    if ip_address in last_search_time:
        time_since_last = (current_time - last_search_time[ip_address]).total_seconds()
        if time_since_last < SEARCH_COOLDOWN:
            return False
    last_search_time[ip_address] = current_time
    return True

def check_tor_link(url):
    """Verify if an onion link is active"""
    session = requests.Session()
    session.proxies = TOR_PROXY
    
    try:
        if not url.startswith('http'):
            url = f'http://{url}'
            
        logging.info(f"Checking link: {url}")
        response = session.head(url, timeout=31)
        is_active = response.status_code == 200
        logging.info(f"Link status: {'ACTIVE' if is_active else 'INACTIVE'} - {url}")
        return is_active
    except Exception as e:
        logging.error(f"Error checking link {url}: {str(e)}")
        return False
        
def marketplace_search(query):
    """
    Returns URLs whose keywords match the query.
    Each URL has associated keywords - returns all matching URLs.
    """
    
    # Predefined set of URLs with their associated keywords
    resource_map = {
        "http://rbcxodz4socx3rupvmhan2d7pvik4dpqmf4kexz6acyxbucf36a6ggid.onion/": ["cannabis", "drugs", "drug"],
        "http://7bw24ll47y7aohhkrfdq2wydg3zvuecvjo63muycjzlbaqlihuogqvyd.onion/": ["drugs", "drug", "cocaine", "mdma crystals","speed","pure crystal meth","stimulants","psychedelics","lsd","mescaline","dmt","ketamine","viagra","prescription","kamagra","cialis","xanax","tramadol","oxycodone"],
        "http://6hzbfxpnsdo4bkplp5uojidkibswevsz3cfpdynih3qvfr24t5qlkcyd.onion/": ["drugs", "drug", "LSD", "mescaline","dmt"],
        "http://wms5y25kttgihs4rt2sifsbwsjqjrx3vtc42tsu2obksqkj7y666fgid.onion/": ["cocaine", "mdma", "drugs","drug","amnesia haze","ketamine","lsd","mdma"],
        "http://gkcns4d3453llqjrksxdijfmmdjpqsykt6misgojxlhsnpivtl3uwhqd.onion/": ["drugs", "drug", "skunk","trainwreck","sour diesel"],
        "http://dumlq77rikgevyimsj6e2cwfsueo7ooynno2rrvwmppngmntboe2hbyd.onion/" : ["drugs","drug","bubblegum","marokk hash"],
        "http://wges3aohuplu6he5tv4pn7sg2qaummlokimim6oaauqo2l7lbx4ufyyd.onion/" : ["buds","oil","ointment","suppositories","creams","soaps","edibles","special offers","bath melts"],
        "http://gn74rz534aeyfxqf33hqg6iuspizulmvpd7zoyz7ybjq4jo3whkykryd.onion/" : ["haze","bubblegum","cannabis","drugs","drug","jack herer","banana kush","blue cheese","chronic","ice-o-lator-hash"],
        "http://4p6i33oqj6wgvzgzczyqlueav3tz456rdu632xzyxbnhq4gpsriirtqd.onion/" : ['drugs','drug','cocaine','prescriptions','speed','cannabis','ecstasy','heroin','bitcoins','services'],
        "http://porf65zpwy2yo4sjvynrl4eylj27ibrmo5s2bozrhffie63c7cxqawid.onion/" : ['drug','drugs','cannabis','haze','kush'],
        "http://c5xoy22aadb2rqgw3jh2m2irmu563evukqqddu5zjandunaimzaye5id.onion/" : ['drugs','drug','cocaine','heroine','mdma','lsd']
        
    }


    normalized_query = query.lower().strip()
    matching_urls = []

    for url, keywords in resource_map.items():
        if any(keyword in normalized_query for keyword in keywords):
            matching_urls.append(url)
    
    return list(matching_urls)


def fetch_onion_links(query, engine_url):
    """Scrape onion links from search engines"""
    try:
        #if threading.active_count() % 3 == 0:
         #   logging.info("Rotating Tor circuit...")
          #  #change_identity()
            
        full_url = f"{engine_url}{query}"
        logging.info(f"-----------------------------------------Checking for Links-----------------------------------------")
        
        response = requests.get(full_url, proxies=TOR_PROXY, timeout=80)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        links = set()
        
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            if ".onion" in href:
                if href.startswith('http'):
                    links.add(href)
                    logging.info(f"--Found onion link--")
                else:
                    normalized = f"http://{href.split('/')[0]}"
                    links.add(normalized)
                    logging.info(f"Normalized onion link: {href} -> {normalized}")
        
        logging.info(f"Found {len(links)} links")
        return list(links)
        
    except Exception as e:
        logging.error(f"Error querying engine: {str(e)}")
        return []
        
def fetch_links_from_engine(engine_name, engine_url, query):
    """Wrapper function for fetch_onion_links to use with threading"""
    try:
        if engine_name in failed_engines:
            logging.info(f"Skipping previously failed engine: {engine_name}")
            return {"engine": engine_name, "links": [], "skipped": True}

        logging.info(f"Querying {engine_name} for '{query}'")
        links = fetch_onion_links(query, engine_url)
        
        if not links:  # If no links found, track failure
            engine_failures[engine_name] = engine_failures.get(engine_name, 0) + 1
            if engine_failures[engine_name] >= 2:  # If engine fails twice
                failed_engines.add(engine_name)
                logging.warning(f"Engine {engine_name} marked as failed")
        else:
            # Reset failure count on success
            engine_failures[engine_name] = 0
            
        return {"engine": engine_name, "links": links}
    except Exception as e:
        logging.error(f"Error in {engine_name} query: {str(e)}")
        engine_failures[engine_name] = engine_failures.get(engine_name, 0) + 1
        if engine_failures[engine_name] >= 2:
            failed_engines.add(engine_name)
        return {"engine": engine_name, "links": [], "error": str(e)}

@app.route("/search", methods=["GET"])
def search():
    query = request.args.get("query", "").strip()
    ip_address = request.remote_addr
    
    logging.info(f"Starting search for: '{query}' from IP: {ip_address}")
    
    if not query:
        logging.warning("Empty query received")
        return jsonify({"error": "Query parameter is required"}), 400

    if not check_rate_limit(ip_address):
        return jsonify({"error": "Please wait before making another search"}), 429

    start_time = time.time()
    results = []
    active_engines = {k: v for k, v in ONION_SEARCH_ENGINES.items() if k not in failed_engines}
    
    try:
        if should_rotate_circuit():
            logging.info("Rotating Tor circuit due to multiple failures")
            if change_identity():
                active_engines = ONION_SEARCH_ENGINES.copy()  # Reset to all engines after rotation
            
        # Use ThreadPoolExecutor to query all search engines in parallel
        with ThreadPoolExecutor(max_workers=min(len(active_engines), 5)) as executor:
            # Submit all search engine queries as separate threads
            future_to_engine = {
                executor.submit(fetch_links_from_engine, engine_name, engine_url, query): engine_name
                for engine_name, engine_url in active_engines.items()
            }
            
            # Process results as they come in
            for future in as_completed(future_to_engine):
                engine_name = future_to_engine[future]
                try:
                    engine_result = future.result()
                    if not engine_result.get("skipped", False):
                        process_links(engine_result["links"], results)
                except Exception as e:
                    logging.error(f"Error processing results from {engine_name}: {str(e)}")
        
        # Search marketplaces with delay to avoid overload
        if results:  # Only search marketplaces if we have some results
            logging.info('Checking marketplaces')
            time.sleep(2)  # Small delay before marketplace search
            marketplace_links = marketplace_search(query)
            process_links(marketplace_links, results)
        
        # If no results found, try rotating circuit and searching marketplaces
        if not results:
            logging.info("No results found, trying marketplace search with new circuit")
            if change_identity():
                marketplace_links = marketplace_search(query)
                process_links(marketplace_links, results)
        
    except Exception as e:
        logging.error(f"Error during search: {str(e)}")
        return jsonify({"error": "An error occurred during search"}), 500

    elapsed_time = round(time.time() - start_time, 2)
    logging.info(f"Search completed in {elapsed_time} seconds with {len(results)} results")
    
    return jsonify({
        "links": results,
        "time_taken": elapsed_time,
        "query": query,
        "active_engines": len(active_engines),
        "total_engines": len(ONION_SEARCH_ENGINES)
    })

def process_links(links, results, max_links=50):
    """Process and validate links with a maximum limit"""
    processed = 0
    for link in links:
        if processed >= max_links:
            break
            
        try:
            status = "active" if check_tor_link(link) else "inactive"
            results.append({"link": link, "status": status})
            logging.info(f"Processed link: {link} ({status})")
            processed += 1
        except Exception as e:
            logging.warning(f"Failed to process link {link}: {str(e)}")
            continue  # Skip failed links


@app.route('/signup', methods=['POST'])
def signup():
    data = request.json
    name = data.get('name')
    email = data.get('email')
    phonenumber = data.get('phonenumber')
    password = data.get('password')

    if not all([name, email, phonenumber, password]):
        return jsonify({"message": "All fields are required"}), 400

    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    if cursor.fetchone():
        return jsonify({"message": "User already exists"}), 400

    # Hash password and store it as a string
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    cursor.execute("INSERT INTO users (name, email, phonenumber, password) VALUES (?, ?, ?, ?)",
                   (name, email, phonenumber, hashed_password))
    conn.commit()
    return jsonify({"message": "User signed up successfully!"}), 201

# Signin route
@app.route('/signin', methods=['POST'])
def signin():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    if not all([email, password]):
        return jsonify({"message": "Email and password are required"}), 400

    cursor.execute("SELECT name, email, phonenumber, password FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    
    if not user or not bcrypt.checkpw(password.encode('utf-8'), user[3].encode('utf-8')):
        return jsonify({"message": "Invalid email or password"}), 401

    return jsonify({"message": "Signin successful!", "user": {"name": user[0], "email": user[1], "phonenumber": user[2]}}), 200
    
@app.route('/')
def home():
    return app.send_static_file('index.html')

@app.route("/suggest", methods=["GET"])
def get_suggestions():
    """Get word suggestions based on the current input"""
    prefix = request.args.get("prefix", "").strip()
    context = request.args.get("context", "")  # Optional context for better AI suggestions
    
    try:
        suggestions = recommendation_system.get_words_with_prefix(prefix)
        return jsonify({
            "suggestions": suggestions,
            "is_ai_powered": True,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        print(f"Error getting suggestions: {e}")
        return jsonify({
            "error": "Failed to get suggestions",
            "suggestions": [],
            "is_ai_powered": False
        }), 500

@app.route("/link_details", methods=["GET"])
def get_link_details():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "URL parameter is required"}), 400

    try:
        details = link_details_manager.get_link_details(url, recommendation_system)
        if "error" in details:
            return jsonify(details), 500
        return jsonify(details)
    except Exception as e:
        logging.error(f"Error getting link details: {str(e)}")
        return jsonify({
            "error": "Failed to fetch link details",
            "snapshot": None,
            "description": f"Error: {str(e)}"
        }), 500

if __name__ == "__main__":
    logging.info("Starting Dark Web Search API")
    app.run(host="0.0.0.0", port=5000, threaded=True)
