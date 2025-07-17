import undetected_chromedriver as uc
import base64
from io import BytesIO
from PIL import Image
import time
import logging
from bs4 import BeautifulSoup
import requests
import shutil
import os

class LinkDetailsManager:
    def __init__(self, tor_proxy=None):
        self.tor_proxy = tor_proxy or {
            "http": "socks5h://127.0.0.1:9050",
            "https": "socks5h://127.0.0.1:9050"
        }
        self.setup_logging()
        self.cleanup_old_drivers()
        self.log_version_info()

    def setup_logging(self):
        """Configure logging for link details operations"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('link_details.log')
            ]
        )
        
    def cleanup_old_drivers(self):
        """Clean up old chromedriver versions"""
        try:
            shutil.rmtree(uc.TEMP_DIR, ignore_errors=True)
            logging.info("Cleaned up old driver versions")
        except Exception as e:
            logging.warning(f"Failed to clean old drivers: {e}")

    def log_version_info(self):
        """Log version information for debugging"""
        try:
            browser_version = uc.get_browser_version()
            logging.info(f"Detected Chrome version: {browser_version}")
        except Exception as e:
            logging.error(f"Version detection failed: {e}")

    def get_chrome_options(self):
        """Configure Chrome options for Tor"""
        chrome_options = uc.ChromeOptions()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--proxy-server=socks5://127.0.0.1:9050')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-popup-blocking')
        return chrome_options
        
    def create_driver(self):
        """Create Chrome driver with version handling"""
        try:
            return uc.Chrome(
                options=self.get_chrome_options(),
                version_main=135,  # Matches your ChromeDriver version
                use_subprocess=True,
                suppress_welcome=True,
                headless=True,
                log_level=logging.WARNING
            )
        except Exception as e:
            logging.error(f"Driver creation failed: {e}")
            # Fallback to automatic version detection
            try:
                return uc.Chrome(
                    options=self.get_chrome_options(),
                    version_main=None,
                    use_subprocess=True
                )
            except Exception as fallback_error:
                logging.critical(f"Fallback driver creation failed: {fallback_error}")
                raise RuntimeError("Failed to initialize Chrome driver")

    def capture_screenshot(self, url):
        """Capture a screenshot of the webpage"""
        driver = None
        try:
            driver = self.create_driver()
            driver.set_page_load_timeout(30)
            
            # Load the page
            driver.get(url)
            time.sleep(5)  # Wait for dynamic content
            
            # Take screenshot
            screenshot = driver.get_screenshot_as_png()
            img = Image.open(BytesIO(screenshot))
            
            # Resize image
            max_width = 800
            if img.size[0] > max_width:
                ratio = max_width / float(img.size[0])
                height = int(float(img.size[1]) * ratio)
                img = img.resize((max_width, height), Image.Resampling.LANCZOS)
            
            # Convert to base64
            buffered = BytesIO()
            img.save(buffered, format="PNG", optimize=True)
            img_str = base64.b64encode(buffered.getvalue()).decode()
            
            return f"data:image/png;base64,{img_str}"
            
        except Exception as e:
            logging.error(f"Screenshot failed for {url}: {str(e)}")
            return None
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass
                    
    def extract_page_content(self, url):
        """Extract text content from the webpage"""
        driver = None
        try:
            driver = self.create_driver()
            driver.set_page_load_timeout(30)
            driver.get(url)
            time.sleep(3)
            
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            for script in soup(["script", "style"]):
                script.decompose()
                
            text = soup.get_text(separator=' ', strip=True)
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            return text[:1000]
            
        except Exception as e:
            logging.error(f"Content extraction failed for {url}: {str(e)}")
            return None
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass
            
    def analyze_content(self, text, recommendation_system):
        """Generate AI analysis of the page content"""
        try:
            if not text:
                return "No content available for analysis."
                
            prompt = (
                "Analyze this dark web page content and provide a detailed but concise description "
                "of what the page appears to be about, including any notable features or warnings: \n\n"
                f"{text}"
            )
            
            description = recommendation_system.get_ai_suggestions("", prompt)
            
            if isinstance(description, list) and len(description) > 0:
                return description[0]
            return description if description else "Analysis unavailable."
                
        except Exception as e:
            logging.error(f"Content analysis failed: {str(e)}")
            return f"Analysis error: {str(e)}"
            
    def get_link_details(self, url, recommendation_system):
        """Get complete details for a link"""
        try:
            logging.info(f"Processing URL: {url}")
            
            screenshot = self.capture_screenshot(url)
            content = self.extract_page_content(url)
            description = self.analyze_content(content, recommendation_system)
            
            return {
                "snapshot": screenshot,
                "description": description,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "status": "success"
            }
            
        except Exception as e:
            logging.error(f"Failed to process {url}: {str(e)}")
            return {
                "error": str(e),
                "snapshot": None,
                "description": f"Error: {str(e)}",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "status": "failed"
            }
