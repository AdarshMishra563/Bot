import os
import requests
import pandas as pd
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

SERPAPI_KEY = os.getenv("SERPAPI_KEY")

def fetch_jobs(query, location="Remote", pages=1):
    print(f"Searching Google Jobs for '{query}' in '{location}'...")
    
    jobs_data = []
    
    for page in range(pages):
        start_index = page * 10
        params = {
            "engine": "google_jobs",
            "q": query,
            "location": location,
            "api_key": SERPAPI_KEY
        }
        
        if start_index > 0:
            params["start"] = start_index
            
        response = requests.get("https://serpapi.com/search", params=params)
        
        if response.status_code != 200:
            print(f"  Error fetching data: HTTP {response.status_code}")
            try:
                print("  Details:", response.json())
            except:
                print("  Details:", response.text)
            break
            
        results = response.json()
        
        if "error" in results:
            print(f"  SerpApi Error: {results['error']}")
            break
            
        if "jobs_results" not in results:
            print(f"  No jobs found for this query in {location}.")
            break
            
        for job in results["jobs_results"]:
            jobs_data.append({
                "Job Title": job.get("title"),
                "Company Name": job.get("company_name"),
                "Location": job.get("location"),
                "Job Link": job.get("share_link", ""),
                "Description": job.get("description", "")[:200] + "...", 
                "HR_Email": "" 
            })
            
        print(f"  Fetched page {page+1}/{pages} ({len(results['jobs_results'])} jobs)")
        
    return jobs_data

if __name__ == "__main__":
    if not SERPAPI_KEY or len(SERPAPI_KEY) < 20:
        print("ERROR: Please set your real SERPAPI_KEY in the .env file.")
    else:
        # Load existing jobs to avoid getting duplicates and to compute how many new ones we fetch
        csv_file = "found_jobs_enriched.csv"
        try:
            df_existing = pd.read_csv(csv_file)
            print(f"Loaded existing enriched CSV with {len(df_existing)} jobs.")
        except FileNotFoundError:
            print("No existing found_jobs_enriched.csv found, starting fresh.")
            df_existing = pd.DataFrame()

        search_queries = [
            "Software Developer Fresher 0 to 1 year experience",
            "Entry Level React Developer",
            "Junior Node.js Developer 0 experience",
            "Python Developer fresher",
            "Junior Software Engineer Entry Level",
        ]
        
        target_locations = [
            "India",
            "Canada"
        ]
        
        all_jobs_data = []
        api_calls_made = 0
        MAX_API_CALLS = 90
        TARGET_NEW_JOBS = 50
        
        print(f"Starting Focused Search for 0-1 Yr Exp Jobs...")
        print(f"Goal: {TARGET_NEW_JOBS} new unique jobs")
        print("=" * 60)
        
        # Track initial known titles/companies to deduplicate safely
        known_signatures = set()
        if not df_existing.empty:
            for _, row in df_existing.iterrows():
                sig = f"{row.get('Job Title','')}|{row.get('Company Name','')}"
                known_signatures.add(sig.lower())

        new_jobs_added = 0

        for location in target_locations:
            if new_jobs_added >= TARGET_NEW_JOBS or api_calls_made >= MAX_API_CALLS:
                break

            for base_query in search_queries:
                if new_jobs_added >= TARGET_NEW_JOBS or api_calls_made >= MAX_API_CALLS:
                    break
                    
                # Modify query for India to strictly look for Remote
                query = base_query + " Remote" if location == "India" else base_query
                    
                print(f"\n--- [{api_calls_made+1}/{MAX_API_CALLS}] '{query}' in '{location}' ---")
                
                # We can fetch multiple pages to hit our 50 faster, but we'll ask for 1 page (10 jobs) per iteration
                found = fetch_jobs(query=query, location=location, pages=1)
                api_calls_made += 1
                
                if found:
                    for job in found:
                        sig = f"{job['Job Title']}|{job['Company Name']}".lower()
                        if sig not in known_signatures:
                            # It's a new job! Ensure format matches enriched csv (includes Email_Sent and HR_Email)
                            job['Email_Sent'] = 'No'
                            all_jobs_data.append(job)
                            known_signatures.add(sig)
                            new_jobs_added += 1

                print(f"New jobs accumulated so far: {new_jobs_added}/{TARGET_NEW_JOBS}")

        if all_jobs_data:
            df_new = pd.DataFrame(all_jobs_data)
            
            # Append new jobs to existing
            if not df_existing.empty:
                df_final = pd.concat([df_existing, df_new], ignore_index=True)
            else:
                df_final = df_new
                
            df_final.to_csv(csv_file, index=False)
            print(f"\n{'=' * 60}")
            print(f"🎉 SEARCH COMPLETE!")
            print(f"   Successfully found and appended {new_jobs_added} NEW unique jobs.")
            print(f"   Total jobs in enriched CSV is now: {len(df_final)}")
            print(f"   API calls used: {api_calls_made}/{MAX_API_CALLS}")
            print(f"   Saved to '{csv_file}'")
            print(f"{'=' * 60}")
        else:
            print("\nDid not find any new unique jobs meeting the criteria.")
