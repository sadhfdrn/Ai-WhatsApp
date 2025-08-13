#!/usr/bin/env python3
import sys
import json
import os
import yt_dlp
import tempfile
import re

def get_actual_tiktok_url(url):
    """Get the actual TikTok URL by following redirects and trying case variations"""
    import requests
    from urllib.parse import urlparse
    
    url = url.strip()
    
    # For shortened URLs, try different case variations if the first fails
    if 'vt.tiktok.com' in url or 'vm.tiktok.com' in url:
        parsed = urlparse(url)
        path_parts = parsed.path.strip('/').split('/')
        
        if len(path_parts) > 0:
            video_id = path_parts[-1]
            urls_to_try = [url]  # Start with original
            
            # Add case variations
            if video_id.islower():
                urls_to_try.append(url.replace(video_id, video_id.upper()))
            elif video_id.isupper():
                urls_to_try.append(url.replace(video_id, video_id.lower()))
            else:
                # Mixed case, try both variations
                urls_to_try.append(url.replace(video_id, video_id.upper()))
                urls_to_try.append(url.replace(video_id, video_id.lower()))
            
            # Try each URL variation
            for test_url in urls_to_try:
                try:
                    response = requests.head(test_url, allow_redirects=True, timeout=10)
                    final_url = response.url
                    
                    # Check if it redirects to a valid video page (not explore/home)
                    if '/video/' in final_url and 'explore' not in final_url:
                        return final_url
                
                except Exception:
                    continue
    
    return url

def download_tiktok_video(url, output_file):
    """Download TikTok video using yt-dlp"""
    try:
        # Clean the URL
        original_url = url.strip()
        
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
        
        # List of URLs to try (original + case variations for shortened URLs)
        urls_to_try = [original_url]
        
        # For shortened URLs, add case variations
        if 'vt.tiktok.com' in original_url or 'vm.tiktok.com' in original_url:
            from urllib.parse import urlparse
            parsed = urlparse(original_url)
            path_parts = parsed.path.strip('/').split('/')
            
            if len(path_parts) > 0:
                video_id = path_parts[-1]
                # Try different case variations
                if video_id != video_id.upper():
                    urls_to_try.append(original_url.replace(video_id, video_id.upper()))
                if video_id != video_id.lower():
                    urls_to_try.append(original_url.replace(video_id, video_id.lower()))
        
        # Try each URL until one works
        last_error = None
        for test_url in urls_to_try:
            try:
                # Extract video info first
                info = None
                with yt_dlp.YoutubeDL({'quiet': True, 'no_warnings': True}) as ydl:
                    info = ydl.extract_info(test_url, download=False)
                
                if not info:
                    continue
                
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
                    ydl.download([test_url])
                
                # If we get here, the download was successful
                break
                
            except Exception as e:
                last_error = str(e)
                if 'Unsupported URL' in last_error and 'explore' in last_error:
                    continue  # Try next URL variation
                else:
                    # For other errors, don't continue trying
                    break
        else:
            # No URL worked
            if last_error:
                if 'explore' in last_error or 'Unsupported URL' in last_error:
                    return {'error': 'Invalid or expired TikTok URL. This could be due to:\n• The video was deleted or made private\n• The shortened URL has expired\n• Incorrect case sensitivity in the URL\n\nPlease:\n• Check if the video is still available on TikTok\n• Try copying the URL directly from the TikTok app\n• Ensure the URL format is correct'}
                else:
                    return {'error': f'Download failed: {last_error}'}
            else:
                return {'error': 'Could not extract video information from any URL variation'}
        
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