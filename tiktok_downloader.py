#!/usr/bin/env python3
import sys
import json
import os
import yt_dlp
import tempfile
import re

def download_tiktok_video(url, output_file):
    """Download TikTok video using yt-dlp"""
    try:
        # Clean the URL
        url = url.strip()
        
        # Ensure output directory exists
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        # Get base filename without extension
        base_name = os.path.splitext(output_file)[0]
        
        # yt-dlp options for TikTok
        ydl_opts = {
            'outtmpl': f'{base_name}.%(ext)s',
            'format': 'best[ext=mp4]/best',  # Prefer mp4 format
            'writesubtitles': False,
            'writeautomaticsub': False,
            'writedescription': False,
            'writeinfojson': False,
            'writethumbnail': False,
            'ignoreerrors': False,
            'no_warnings': False,
            'extractflat': False,
            'retries': 3,
            'socket_timeout': 30,
        }
        
        # Extract video info first
        info = None
        with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True}) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
            except Exception as e:
                return {'error': f'Failed to extract video info: {str(e)}'}
        
        if not info:
            return {'error': 'Could not extract video information'}
        
        # Get video details
        title = info.get('title', 'TikTok Video')
        uploader = info.get('uploader', 'Unknown')
        video_id = info.get('id', 'unknown')
        duration = info.get('duration', 0)
        
        # Clean title for safer filename
        safe_title = re.sub(r'[^\w\s-]', '', title).strip()
        safe_title = re.sub(r'[-\s]+', '-', safe_title)[:50]  # Limit length
        
        # Download the video
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        # Find the downloaded file (yt-dlp might add extension)
        downloaded_file = None
        possible_extensions = ['.mp4', '.webm', '.mkv', '.flv']
        
        for ext in possible_extensions:
            test_file = f"{base_name}{ext}"
            if os.path.exists(test_file):
                downloaded_file = test_file
                break
        
        if not downloaded_file or not os.path.exists(downloaded_file):
            return {'error': 'Downloaded file not found after download'}
        
        # If the downloaded file has a different name than expected, rename it
        if downloaded_file != output_file:
            try:
                if os.path.exists(output_file):
                    os.remove(output_file)
                os.rename(downloaded_file, output_file)
                downloaded_file = output_file
            except OSError:
                # If rename fails, keep the original name
                pass
        
        file_size = os.path.getsize(downloaded_file)
        
        return {
            'success': True,
            'title': title,
            'author': uploader,
            'video_id': video_id,
            'duration': duration,
            'file_size': file_size,
            'output_file': downloaded_file
        }
        
    except yt_dlp.utils.DownloadError as e:
        error_msg = str(e)
        if 'Video unavailable' in error_msg:
            return {'error': 'Video is unavailable or private'}
        elif 'network' in error_msg.lower():
            return {'error': 'Network error - check internet connection'}
        else:
            return {'error': f'Download failed: {error_msg}'}
    except Exception as e:
        return {'error': f'Unexpected error: {str(e)}'}

def main():
    if len(sys.argv) != 3:
        print(json.dumps({'error': 'Usage: python3 tiktok_downloader.py <url> <output_file>'}))
        sys.exit(1)
    
    url = sys.argv[1]
    output_file = sys.argv[2]
    
    # Download video using yt-dlp
    result = download_tiktok_video(url, output_file)
    
    if 'error' in result:
        print(json.dumps(result))
        sys.exit(1)
    
    # Return success info
    print(json.dumps(result))

if __name__ == '__main__':
    main()