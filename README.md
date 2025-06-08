# 🚀 AI-Powered-DarkWeb-Search
The project leverages Open Source Intelligence (OSINT) methodologies to gather actionable intelligence from the Dark Web, accessed exclusively via the Tor network. To enhance the efficiency and analytical depth of the OSINT operations a Word Recommendation System in the Search Bar and AI-Powered Link Analysis functionality is added.
## 📖 Setup Instructions (Linux)
### Step 1: Locate and Configure Your torrc File
You need to configure Tor to expose additional SOCKS ports, which your application will use.

Open your terminal.

Open the torrc file using sudo with a text editor (like nano, mousepad):
##### sudo nano /etc/tor/torrc
Add or uncomment the following lines in the torrc file:

##### SocksPort 9050

##### SocksPort 9051

Save the file and exit the text editor.

SocksPort 9050: This is the default Tor SOCKS proxy port.

SocksPort 9051: This adds an additional SOCKS proxy port, which can be useful for certain applications or for load balancing if your project uses multiple Tor connections.

### Step 2: Restart Tor Services
After modifying the torrc file, you must restart the Tor service for the changes to take effect.

In your terminal, run:

##### sudo systemctl restart tor

### Step 3: Verify Internet Connection
Before proceeding, ensure your system has an active internet connection.
Open your terminal.
Run the following command:

##### ping abc.com

If you see replies, your internet connection is active.
If you see "Request timed out" or "Destination host unreachable," troubleshoot your network connection.

### Step 4: Install Project Dependencies
The project relies on several Python libraries. Install them using pip.
Navigate to the project's root directory (where requirements.txt is located) in your terminal.
Run the following command:

##### pip install -r requirements.txt

### Step 5: Start Tor Services
Even if you restarted Tor in Step 2, it's good practice to ensure it's running before launching the application.
In your terminal, run:

##### sudo systemctl start tor

### Step 6: Run the Application
Finally, launch the main application file.
From the project's root directory in your terminal, run:

##### python app.py

Your Dark Web OSINT application should now be running.
