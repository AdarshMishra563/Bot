import os
import re
import time
import requests
import pandas as pd
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

APOLLO_API_KEY = os.getenv("APOLLO_API_KEY")

# ============================================================
# LAYER 0: Find the real company domain using Clearbit (FREE)
# ============================================================
def get_company_domain(company_name):
    """Uses Clearbit's free autocomplete to find the real website domain."""
    try:
        url = f"https://autocomplete.clearbit.com/v1/companies/suggest?query={company_name}"
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            data = res.json()
            if len(data) > 0:
                return data[0]['domain']
    except Exception as e:
        print(f"    [Clearbit] Error: {e}")
    return None

# ============================================================
# LAYER 1: Apollo API - Find actual HR person emails
# ============================================================
def find_email_apollo(company_name, domain):
    """Search Apollo for HR/Recruiter contacts at the company."""
    if not APOLLO_API_KEY:
        return None
        
    print(f"    [Apollo] Searching for HR contacts at {domain}...")
    url = "https://api.apollo.io/v1/mixed_people/search"
    
    headers = {
        "Content-Type": "application/json",
        "Cache-Control": "no-cache",
        "api-key": APOLLO_API_KEY
    }

    data = {
        "q_organization_domains": domain,
        "person_titles": [
            "HR", "Human Resources", "Recruiter", 
            "Talent Acquisition", "Technical Recruiter",
            "People Operations", "Hiring Manager"
        ],
        "page": 1,
        "per_page": 3  # Get up to 3 contacts
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=15)
        if response.status_code == 200:
            result = response.json()
            if result.get("people"):
                emails = []
                for person in result["people"]:
                    email = person.get("email")
                    if email:
                        name = person.get("name", "Unknown")
                        title = person.get("title", "Unknown")
                        print(f"    [Apollo] Found: {name} ({title}) -> {email}")
                        emails.append(email)
                if emails:
                    return emails[0]  # Return the best match
        elif response.status_code == 429:
            print("    [Apollo] Rate limit hit. Waiting 60s...")
            time.sleep(60)
    except Exception as e:
        print(f"    [Apollo] Error: {e}")
    
    return None

# ============================================================
# LAYER 2: Hunter.io - Find verified emails for a domain (FREE)
# ============================================================
def find_email_hunter(domain):
    """Uses Hunter.io's free domain search (no API key needed for public data)."""
    print(f"    [Hunter] Searching verified emails for {domain}...")
    try:
        # Hunter.io public email finder
        url = f"https://api.hunter.io/v2/domain-search?domain={domain}&limit=5"
        
        # Check if user has a Hunter API key (optional)
        hunter_key = os.getenv("HUNTER_API_KEY", "")
        if hunter_key:
            url += f"&api_key={hunter_key}"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                emails_data = data.get("data", {}).get("emails", [])
                for e in emails_data:
                    email = e.get("value")
                    if email:
                        print(f"    [Hunter] Found verified: {email}")
                        return email
    except Exception as e:
        print(f"    [Hunter] Error: {e}")
    
    return None

# ============================================================
# LAYER 3: Web Scraper - Visit the company website directly
# ============================================================
def find_email_scraper(domain):
    """Visits the company website and scrapes email addresses from the HTML."""
    print(f"    [Scraper] Visiting {domain} to find emails...")
    
    # Common pages where companies list contact emails
    pages_to_check = [
        f"https://{domain}",
        f"https://{domain}/contact",
        f"https://{domain}/contact-us",
        f"https://{domain}/about",
        f"https://{domain}/careers",
        f"https://{domain}/jobs",
        f"https://www.{domain}",
        f"https://www.{domain}/contact",
        f"https://www.{domain}/careers",
    ]
    
    # Regex pattern to find email addresses in HTML
    email_pattern = re.compile(
        r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        re.IGNORECASE
    )
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    found_emails = set()
    
    for page_url in pages_to_check:
        try:
            resp = requests.get(page_url, headers=headers, timeout=8, allow_redirects=True)
            if resp.status_code == 200:
                # Find all email-like strings in the page
                matches = email_pattern.findall(resp.text)
                for email in matches:
                    # Filter out junk (image files, CSS files, etc.)
                    junk_keywords = ['.png', '.jpg', '.gif', '.svg', '.css', '.js', '.webp', '.woff', '2x.jpg', '.hpetransform']
                    if not any(keyword in email.lower() for keyword in junk_keywords):
                        # Prioritize HR/careers related emails
                        found_emails.add(email.lower())
        except Exception:
            continue  # Page doesn't exist or timed out, try next
    
    if found_emails:
        # Prioritize HR-related emails
        priority_keywords = ['career', 'hr', 'recruit', 'talent', 'job', 'hiring', 'people', 'info', 'contact']
        
        for email in found_emails:
            for keyword in priority_keywords:
                if keyword in email:
                    print(f"    [Scraper] Found priority email: {email}")
                    return email
        
        # If no priority email found, return the first one that isn't a noreply
        for email in found_emails:
            if 'noreply' not in email and 'no-reply' not in email:
                print(f"    [Scraper] Found email: {email}")
                return email
    
    return None

# ============================================================
# MAIN: 3-Layer Smart Email Finder Pipeline
# ============================================================
def find_best_email(company_name):
    """
    Tries 3 different methods to find the best email:
    1. Apollo API (database of 220M contacts)
    2. Hunter.io (verified email database)
    3. Web Scraper (visits the actual company website)
    """
    print(f"\n🔍 Searching email for: {company_name}")
    
    # Step 0: Find the real domain
    domain = get_company_domain(company_name)
    if not domain:
        print(f"  ❌ Could not find website for '{company_name}'. Skipping.")
        return None
    
    print(f"  ✅ Real domain: {domain}")
    
    # Layer 1: Try Apollo
    email = find_email_apollo(company_name, domain)
    if email:
        print(f"  🎯 FOUND via Apollo: {email}")
        return email
    
    # Layer 2: Try Hunter.io
    email = find_email_hunter(domain)
    if email:
        print(f"  🎯 FOUND via Hunter: {email}")
        return email
    
    # Layer 3: Try Web Scraping
    email = find_email_scraper(domain)
    if email:
        print(f"  🎯 FOUND via Web Scraper: {email}")
        return email
    
    print(f"  ❌ No email found for {company_name} across all 3 methods.")
    return None

# ============================================================
# Process the jobs CSV
# ============================================================
def process_jobs():
    try:
        df = pd.read_csv("found_jobs_enriched.csv", dtype={"HR_Email": str})
    except FileNotFoundError:
        print("ERROR: found_jobs_enriched.csv not found! Run job_scraper.py first.")
        return

    print(f"Loaded {len(df)} jobs. Starting 3-layer smart email enrichment...\n")

    found_count = 0
    for index, row in df.iterrows():
        # If email is already filled, skip
        if pd.notna(row["HR_Email"]) and str(row["HR_Email"]).strip() != "":
            found_count += 1
            continue
            
        company = row["Company Name"]
        if company:
            email = find_best_email(company)
            if email:
                df.at[index, "HR_Email"] = email
                found_count += 1
            
            # Brief pause between companies to be respectful
            time.sleep(1)
    
    # Save the enriched CSV
    df.to_csv("found_jobs_enriched.csv", index=False)
    total = len(df)
    print(f"\n{'='*50}")
    print(f"Process complete! Found emails for {found_count}/{total} companies.")
    print(f"Saved to 'found_jobs_enriched.csv'.")
    print(f"{'='*50}")

if __name__ == "__main__":
    if not APOLLO_API_KEY or len(APOLLO_API_KEY) < 10:
        print("WARNING: APOLLO_API_KEY not set. Will skip Apollo and use Hunter + Web Scraper only.")
    process_jobs()
