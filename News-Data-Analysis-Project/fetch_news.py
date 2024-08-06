import pandas as pd
import json
import requests
import datetime
from datetime import date
import uuid
import os
from google.cloud import storage

def upload_to_gcs(bucket_name, destination_blob_name, source_file_name):
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(source_file_name)
    print(f"File {source_file_name} uploaded to {destination_blob_name}.")

def fetch_news_data():
    today = date.today()
    api_key = 'e99d34792cfc4f648e9fcc6e7ea7b026'

    base_url = "https://newsapi.org/v2/everything?q={}&from={}&to={}&sortBy=popularity&apiKey={}&language=en"
    start_date_value = str(today - datetime.timedelta(days=1))
    end_date_value = str(today)

    df = pd.DataFrame(columns=['newsTitle', 'timestamp', 'url_source', 'content', 'source', 'author', 'urlToImage'])

    url_extractor = base_url.format("apple", start_date_value, end_date_value, api_key)
    response = requests.get(url_extractor)
    
    if response.status_code != 200:
        print(f"API request failed with status code {response.status_code}")
        return

    try:
        d = response.json()
    except ValueError as e:
        print(f"Error parsing JSON response: {e}")
        return

    if 'articles' not in d:
        print("'articles' key not found in the response")
        return

    for i in d['articles']:
        newsTitle = i.get('title', 'N/A')
        timestamp = i.get('publishedAt', 'N/A')
        url_source = i.get('url', 'N/A')
        source = i.get('source', {}).get('name', 'N/A')
        author = i.get('author', 'N/A')
        urlToImage = i.get('urlToImage', 'N/A')
        partial_content = i.get('content', '')

        if len(partial_content) >= 200:
            partial_content = partial_content[:199]
        if '.' in partial_content:
            trimmed_part = partial_content[:partial_content.rindex('.')]
        else:
            trimmed_part = partial_content

        new_row = pd.DataFrame({
            'newsTitle': [newsTitle],
            'timestamp': [timestamp],
            'url_source': [url_source],
            'content': [trimmed_part],
            'source': [source],
            'author': [author],
            'urlToImage': [urlToImage]
        })

        df = pd.concat([df, new_row], ignore_index=True)

    current_time = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    filename = f'run_{current_time}.parquet'
    print(df)
    
    # Check and print the current working directory
    print("Current Working Directory:", os.getcwd())

    # Write DataFrame to Parquet file
    df.to_parquet(filename)

    # Upload to GCS
    bucket_name = 'public_pipe_data'
    destination_blob_name = f'news_data_analysis/parquet_files/{filename}'
    upload_to_gcs(bucket_name, destination_blob_name, filename)

    # Remove local file after upload
    os.remove(filename)

# Call the function to test
fetch_news_data()