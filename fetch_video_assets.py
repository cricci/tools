#!/usr/bin/env python3
import os
import re
import requests
from urllib.parse import urljoin, urlparse

#
# If you need a single video file, or a file per format, after this script
#  ffmpeg -i file.m3u8 -c copy TS_concat.mkv (or mp4, or ..), and/or use VLC
# 
# Or, skip this script (the download) and:
#  (alt) ffmpeg -i "http://www.website.com/file.m3u8" -c copy TS_concat.mkv (or mp4, or..)
#
# However, possible you'll need the header/cookie values. So, do that..
#

def extract_headers(curl_command):
    """
    Extract headers from a given cURL string.

    Args:
    curl_command (str): The cURL string.

    Returns:
    dict: A dictionary of headers.
    """
    header_pattern = r'-H\s*[\'"]?([^\'"]+)[\'"]?'
    headers = re.findall(header_pattern, curl_command)
    header_dict = {header.split(": ", 1)[0]: header.split(": ", 1)[1] for header in headers}
    return header_dict

def extract_url(curl_command):
    """
    Extract the URL from a given cURL string and ensure it is an .m3u8 file.

    Args:
    curl_command (str): The cURL string.

    Returns:
    str: The URL found in the cURL string.

    Raises:
    ValueError: If the URL does not point to an .m3u8 file.
    """
    url_pattern = r'curl\s+[\'"]?(https?://[^\s\'"]+)[\'"]?'
    match = re.search(url_pattern, curl_command)
    
    if match:
        url = match.group(1)
        if not url.split('?')[0].endswith('.m3u8'):
            raise ValueError("The URL does not point to an .m3u8 file.")
        return url
    else:
        raise ValueError("No URL found in the cURL command.")

def find_references(content, base_url, file_extension):
    """
    Find file references with a specific extension (e.g., .m3u8, .ts) in the content.

    Args:
    content (str): The content of the file.
    base_url (str): The base URL of the original file.
    file_extension (str): The file extension to search for (e.g., .m3u8, .ts).

    Returns:
    list: A list of URLs found in the content.
    """
    pattern = fr'^(?!#)(.*\{file_extension}(?:\?.*)?)$'
    matches = re.findall(pattern, content, re.MULTILINE)
    urls = [urljoin(base_url, match.strip()) for match in matches]
    return urls

def fetch_file(url, headers):
    """
    Fetch the content of a file from a given URL and headers.

    Args:
    url (str): The URL of the file.
    headers (dict): The headers for the request.

    Returns:
    str: The content of the file.

    Raises:
    Exception: If the request fails or the file cannot be retrieved.
    """
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.text
    else:
        raise Exception(f"Failed to retrieve file from {url}. Status code: {response.status_code}")

def download_file(url, headers, save_path):
    """
    Download a file and save it to the given path.

    Args:
    url (str): The URL of the file.
    headers (dict): The headers for the request.
    save_path (str): The path where the file should be saved.

    Returns:
    None
    """
    response = requests.get(url, headers=headers, stream=True)
    if response.status_code == 200:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Saved: {save_path}")
    else:
        print(f"Failed to download {url}. Status code: {response.status_code}")

def get_filename_from_url(url):
    """
    Extract a file name from a URL, handling query strings.

    Args:
    url (str): The URL to extract the file name from.

    Returns:
    str: The extracted file name.
    """
    parsed_url = urlparse(url)
    filename = os.path.basename(parsed_url.path)
    return filename if filename else 'index.m3u8'

def fetch_and_save_m3u8_and_ts(curl_command, save_directory='downloads'):
    """
    Fetch all .m3u8 files and their referenced .ts files using the headers from a cURL string,
    and save them locally.

    Args:
    curl_command (str): The cURL string.
    save_directory (str): The root directory to save the downloaded files.

    Returns:
    None
    """
    headers = extract_headers(curl_command)
    initial_url = extract_url(curl_command)

    m3u8_files = [initial_url]
    ts_files = []

    for m3u8_url in m3u8_files:
        try:
            # Fetch the content of the .m3u8 file
            content = fetch_file(m3u8_url, headers)
            
            # Save the .m3u8 file locally
            m3u8_filename = get_filename_from_url(m3u8_url)
            # Replace '' w/ subdir if you want m3u8 files in a separate location
            m3u8_save_path = os.path.join(save_directory, '', m3u8_filename)
            os.makedirs(os.path.dirname(m3u8_save_path), exist_ok=True)
            with open(m3u8_save_path, 'w') as f:
                f.write(content)
            print(f"Saved .m3u8 file: {m3u8_save_path}")
            
            # Find additional .m3u8 files and .ts files
            referenced_m3u8_files = find_references(content, m3u8_url, ".m3u8")
            referenced_ts_files = find_references(content, m3u8_url, ".ts")

            # Extend the list of files to fetch
            m3u8_files.extend(referenced_m3u8_files)
            ts_files.extend(referenced_ts_files)
        
        except Exception as e:
            print(f"Error fetching {m3u8_url}: {str(e)}")
    
    # Now download all the .ts files
    for ts_url in ts_files:
        try:
            ts_filename = get_filename_from_url(ts_url)
            # Replace '' w/ subdir if you want ts files in a separate location
            ts_save_path = os.path.join(save_directory, '', ts_filename) 
            download_file(ts_url, headers, ts_save_path)
        except Exception as e:
            print(f"Error downloading {ts_url}: {str(e)}")

def main():
    # Example cURL string (with an .m3u8 URL and a query string)
    # curl_string = ''' [[replace]] '''
    curl_string = input("Enter the cURL string, to the master m3u8: ")

    # Fetch and save all .m3u8 and .ts files
    fetch_and_save_m3u8_and_ts(curl_string)

if __name__ == '__main__':
    main()
