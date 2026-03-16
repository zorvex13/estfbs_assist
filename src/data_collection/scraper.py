import requests
import pdfplumber
import io
from bs4 import BeautifulSoup
import os

def extract_text_from_pdf_url(url, start_page=None, end_page=None):
    """Downloads a PDF from a URL and extracts text from specified pages."""
    print(f"Downloading PDF from: {url}...")
    # Using verify=False just in case the university SSL certificate is acting up
    response = requests.get(url, verify=False) 
    
    if response.status_code == 200:
        extracted_text = ""
        with pdfplumber.open(io.BytesIO(response.content)) as pdf:
            total_pages = len(pdf.pages)
            start_idx = (start_page - 1) if start_page else 0
            end_idx = end_page if end_page else total_pages
            
            for i in range(start_idx, end_idx):
                text = pdf.pages[i].extract_text()
                if text:
                    extracted_text += f"\n--- Page {i + 1} ---\n{text}"
        return extracted_text
    else:
        return f"Failed to download PDF. Status: {response.status_code}"

def extract_text_from_html(url):
    """Fetches a webpage and extracts clean text from it."""
    print(f"Fetching HTML from: {url}...")
    response = requests.get(url, verify=False)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements so we don't get junk code in our text
        for script in soup(["script", "style"]):
            script.extract()
            
        # Extract text and clean up empty lines
        text = soup.get_text(separator='\n')
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        cleaned_text = '\n'.join(chunk for chunk in chunks if chunk)
        
        return cleaned_text
    else:
        return f"Failed to fetch HTML. Status: {response.status_code}"

# ==========================================
# EXECUTION
# ==========================================

# 1. Links
url_cnpn = "https://www.usms.ac.ma/sites/default/files/CNPN2025/CNPN_Dipl%C3%B4me%20Universitaire%20de%20Technologie.pdf"
url_reglement = "https://estfbs.usms.ac.ma/wp-content/uploads/2021/03/Reglement-Interieur-EST-FBS.pdf"
url_website = "https://estfbs.usms.ac.ma/?page_id=10"

# 2. Extract Data
text_cnpn = extract_text_from_pdf_url(url_cnpn, start_page=5, end_page=10)
text_reglement = extract_text_from_pdf_url(url_reglement)
text_website = extract_text_from_html(url_website)

# 3. Save to data/raw/
# Ensure the directory exists just in case
os.makedirs("data/raw", exist_ok=True) 

output_path = "data/raw/est_fbs_data.txt"
with open(output_path, "w", encoding="utf-8") as file:
    file.write("=== CNPN DOCUMENT (Pages de 5 a 10) ===\n")
    file.write(text_cnpn)
    file.write("\n\n=== EST FBS PRESENTATION PAGE ===\n")
    file.write(text_website)
    file.write("\n\n=== REGLEMENT INTERIEUR ===\n")
    file.write(text_reglement)

print(f"\nSuccess! All extracted text has been safely saved to: {output_path}")