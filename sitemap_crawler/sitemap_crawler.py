import requests
import xml.etree.ElementTree as ET
import csv
import logging
from os import path
from datetime import datetime

from config.core import config

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_sitemap_urls(url, limit=None):
    try:
        response = requests.get(url)
        root = ET.fromstring(response.content)
    except requests.RequestException as e:
        logging.error(f"Error fetching sitemap: {url}. Error: {e}")
        raise
    except ET.ParseError as e:
        logging.error(f"Error parsing sitemap: {url}. Error: {e}")
        raise

    all_urls = []

    if root.tag.endswith('sitemapindex'):
        sitemaps = list(root)[:limit]  # Apply the limit here
        logging.info(f"Processing sitemap index with {len(sitemaps)} sitemaps.")
        for i, sitemap in enumerate(sitemaps, 1):
            sitemap_url = sitemap.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc').text
            logging.info(f"Processing sitemap {i}/{len(sitemaps)}: {sitemap_url}")
            all_urls.extend(process_single_sitemap(sitemap_url))
    else:
        logging.info("Processing direct sitemap.")
        all_urls.extend(process_single_sitemap(url))

    return all_urls

def process_single_sitemap(sitemap_url):
    try:
        sitemap_response = requests.get(sitemap_url)
        sitemap_tree = ET.fromstring(sitemap_response.content)
        return [(url.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc').text, 
                 url.find('{http://www.sitemaps.org/schemas/sitemap/0.9}lastmod').text) for url in sitemap_tree]
    except requests.RequestException as e:
        logging.error(f"Error fetching sitemap: {sitemap_url}. Error: {e}")
        raise
    except ET.ParseError as e:
        logging.error(f"Error parsing sitemap: {sitemap_url}. Error: {e}")
        raise

def parse_date(date_str):
    """
    Parse a date string considering multiple potential formats, including with timezone and milliseconds.
    """
    for fmt in ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S.%f%z"):
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Date format not recognized: {date_str}")

def update_master_csv(urls, master_filename):
    """
    Update the master CSV file with the latest URLs and their dates.
    """
    master_data = {}
    if path.exists(master_filename):
        with open(master_filename, 'r', newline='', encoding='utf-8') as file:
            for row in csv.reader(file):
                if len(row) == 2:
                    master_data[row[0]] = row[1]

    # Add new URLs to the master file
    for url, date in urls:
        if url not in master_data:
            master_data[url] = date


    # Write updated data back to the master file
    with open(master_filename, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        for url, date in master_data.items():
            writer.writerow([url, date])

def generate_date_based_csvs(master_filename):
    """
    Generate date-based CSV files from the master CSV file, with URLs sorted alphabetically.
    """
    urls_by_date = {}
    with open(master_filename, 'r', newline='', encoding='utf-8') as file:
        for url, date in csv.reader(file):
            urls_by_date.setdefault(date, set()).add(url)

    for date, urls in urls_by_date.items():
        sorted_urls = sorted(urls)  # Sort the URLs alphabetically
        filename = f'out/sitemap_urls_{date}.csv'
        with open(filename, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            for url in sorted_urls:
                writer.writerow([url])

def process_sitemap(url, limit=None, master_filename='out/master_sitemap.csv'):
    try:
        logging.info("Starting sitemap processing.")
        urls = fetch_sitemap_urls(url, limit)
        logging.info("Sitemap processing complete. Updating master CSV file.")

        urls = [(url, parse_date(date_str).isoformat()) for url, date_str in urls]
        update_master_csv(urls, master_filename)

        logging.info("Master CSV file update complete. Generating date-based CSV files.")
        generate_date_based_csvs(master_filename)
        logging.info("Date-based CSV file generation complete.")
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return

# Get configuration
sitemap_urls = config.sitemap_urls
csv_location = config.csv_location
sitemap_limit = config.sitemap_limit
master_filename = path.join(csv_location, config.master_filename)

# Process the sitemap
for sitemap_url in sitemap_urls:
    process_sitemap(sitemap_url, sitemap_limit)
