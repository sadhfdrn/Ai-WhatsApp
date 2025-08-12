#!/usr/bin/env python3
import sys
import json
import os
import tempfile
import requests
from urllib.parse import urlparse
import re

def get_tiktok_video_info(url):
    """Extract TikTok video information and download URL"""
    try:
        # Clean the URL
        url = url.strip()
        
        # Handle shortened URLs
        if 'vm.tiktok.com' in url or 'vt.tiktok.com' in url:
            # Follow redirects to get full URL
            response = requests.head(url, allow_redirects=True)
            url = response.url
        
        # Extract video ID from URL
        video_id_match = re.search(r'/video/(\d+)', url)
        if not video_id_match:
            return {'error': 'Could not extract video ID from URL'}
        
        video_id = video_id_match.group(1)
        
        # Use TikTok's oEmbed API (public API)
        oembed_url = f"https://www.tiktok.com/oembed?url={url}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(oembed_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # Extract thumbnail URL which often contains the video URL pattern
            thumbnail_url = data.get('thumbnail_url', '')
            title = data.get('title', 'TikTok Video')
            author = data.get('author_name', 'Unknown')
            
            # Try to construct video URL from thumbnail pattern
            if thumbnail_url:
                # TikTok video URLs often follow a pattern
                video_url = thumbnail_url.replace('~tplv-', '~noop').replace('.jpeg', '.mp4').replace('.webp', '.mp4')
                
                # Test if video URL is accessible
                video_response = requests.head(video_url, headers=headers, timeout=5)
                if video_response.status_code == 200:
                    return {
                        'success': True,
                        'video_url': video_url,
                        'title': title,
                        'author': author,
                        'video_id': video_id
                    }
        
        # Fallback: try alternative method
        return {'error': 'Could not extract video URL. TikTok may have changed their API.'}
        
    except requests.RequestException as e:
        return {'error': f'Network error: {str(e)}'}
    except Exception as e:
        return {'error': f'Extraction failed: {str(e)}'}

def download_video(video_url, output_path):
    """Download video from direct URL"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://www.tiktok.com/'
        }
        
        response = requests.get(video_url, headers=headers, stream=True, timeout=30)
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        return {'success': True, 'file_size': os.path.getsize(output_path)}
        
    except Exception as e:
        return {'error': f'Download failed: {str(e)}'}

def main():
    if len(sys.argv) != 3:
        print(json.dumps({'error': 'Usage: python3 tiktok_downloader.py <url> <output_file>'}))
        sys.exit(1)
    
    url = sys.argv[1]
    output_file = sys.argv[2]
    
    # Get video info
    info = get_tiktok_video_info(url)
    
    if 'error' in info:
        print(json.dumps(info))
        sys.exit(1)
    
    # Download video
    download_result = download_video(info['video_url'], output_file)
    
    if 'error' in download_result:
        print(json.dumps(download_result))
        sys.exit(1)
    
    # Return success info
    result = {
        'success': True,
        'title': info['title'],
        'author': info['author'],
        'video_id': info['video_id'],
        'file_size': download_result['file_size'],
        'output_file': output_file
    }
    
    print(json.dumps(result))

if __name__ == '__main__':
    main()