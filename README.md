# 🚀 AI-Powered Dark Web Search

The project leverages **Open Source Intelligence (OSINT)** methodologies to gather actionable intelligence from the Dark Web, accessed exclusively via the Tor network. To enhance efficiency and analytical depth, a **Word Recommendation System** in the search bar and **AI-Powered Link Analysis** functionality have been integrated.

---

## 📖 Setup Instructions (Linux)

### 🔧 Step 1: Locate and Configure Your `torrc` File

Configure Tor to expose additional SOCKS ports that your application will use.

1. Open your terminal.
2. Edit the `torrc` file using a text editor:
   ```bash
   sudo nano /etc/tor/torrc
Add or uncomment the following lines:

SocksPort 9050
SocksPort 9051
SocksPort 9050: Default Tor SOCKS proxy port.

SocksPort 9051: Additional SOCKS proxy port, useful for load balancing or multiple Tor connections.

Save the file and exit the text editor.

🔄 Step 2: Restart Tor Services
After modifying the torrc file, restart the Tor service to apply the changes:

bash
Copy
Edit
sudo systemctl restart tor
🌐 Step 3: Verify Internet Connection
Before proceeding, ensure your system has an active internet connection:

bash
Copy
Edit
ping abc.com
If you see replies, your internet connection is active.

If you see "Request timed out" or "Destination host unreachable," troubleshoot your network connection.

📦 Step 4: Install Project Dependencies
The project relies on several Python libraries. Install them using pip:

Navigate to the project's root directory (where requirements.txt is located):

bash
Copy
Edit
cd /path/to/your/project
Install the dependencies:

bash
Copy
Edit
pip install -r requirements.txt
▶️ Step 5: Start Tor Services
Even if you restarted Tor in Step 2, it’s good practice to ensure it’s running before launching the application:

bash
Copy
Edit
sudo systemctl start tor
🚀 Step 6: Run the Application
Finally, launch the main application file:

bash
Copy
Edit
python app.py
Your AI-Powered Dark Web OSINT application should now be running! 🎉
