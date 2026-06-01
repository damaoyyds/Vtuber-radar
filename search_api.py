import requests
import json
import os
import re
from urllib.parse import urlparse, parse_qs

ORGANIZATIONS = {
    "1001": {
        "name": "四禧丸子",
        "author_ids": "1,10029,10030,10028"
    },
    "1015": {
        "name": "星瞳",
        "author_ids": "10031"
    }
}

def get_organizations():
    return ORGANIZATIONS

def parse_bilibili_url(play_url):
    if not play_url:
        return None
    
    parsed = urlparse(f"http://{play_url}")
    query_params = parse_qs(parsed.query)
    
    bvid = query_params.get('bvid', [None])[0]
    p = query_params.get('p', [None])[0]
    
    if bvid:
        if p and p.isdigit():
            p = p.lstrip('0')
            if not p:
                p = '1'
            return f"https://www.bilibili.com/video/{bvid}/?p={p}"
        else:
            return f"https://www.bilibili.com/video/{bvid}/"
    
    return None

def fetch_subtitles(clip_id, keyword):
    url = f"https://api.zimu.live:7443/clips/{clip_id}/subtitles"
    
    params = {
        "keyword": keyword
    }
    
    headers = {
        "Accept": "application/json, text/plain, */*",
        "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Mobile Safari/537.36"
    }
    
    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def find_matching_subtitles(clip_id, keyword):
    subtitles_data = fetch_subtitles(clip_id, keyword)
    if "error" in subtitles_data:
        return []
    
    matches = []
    if "data" in subtitles_data and "subtitles" in subtitles_data["data"]:
        for subtitle in subtitles_data["data"]["subtitles"]:
            marked_content = subtitle.get("marked_content", "")
            start = subtitle.get("start", 0)
            end = subtitle.get("end", 0)
            
            pinyin_match = re.search(r'<pinyin>(.*?)</pinyin>', marked_content)
            text_match = re.search(r'<text>(.*?)</text>', marked_content)
            
            if pinyin_match or text_match:
                clean_content = marked_content
                if pinyin_match:
                    clean_content = clean_content.replace(f'<pinyin>{pinyin_match.group(1)}</pinyin>', pinyin_match.group(1))
                if text_match:
                    clean_content = clean_content.replace(f'<text>{text_match.group(1)}</text>', text_match.group(1))
                
                matches.append({
                    "clip_id": clip_id,
                    "start": start,
                    "end": end,
                    "marked_content": marked_content,
                    "clean_content": clean_content,
                    "pinyin": pinyin_match.group(1) if pinyin_match else "",
                    "text": text_match.group(1) if text_match else ""
                })
    
    return matches

def fetch_search_results(keyword, org_ids, page=1, page_size=10):
    if not org_ids:
        return {"error": "请至少选择一个组织"}
    
    results = []
    for org_id in org_ids:
        org_info = ORGANIZATIONS.get(org_id)
        if not org_info:
            continue
        
        url = f"https://api.zimu.live:7443/organizations/{org_id}/clips"
        
        params = {
            "page": page,
            "page_size": page_size,
            "author_ids": org_info["author_ids"],
            "keyword": keyword,
            "start_date": "2026-03-01",
            "end_date": "2026-06-01"
        }
        
        headers = {
            "Accept": "application/json, text/plain, */*",
            "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Mobile Safari/537.36"
        }
        
        try:
            response = requests.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()
            if "data" in data and "items" in data["data"]:
                for item in data["data"]["items"]:
                    item["org_name"] = org_info["name"]
                    item["org_id"] = org_id
                    item["bilibili_url"] = parse_bilibili_url(item.get("play_url", ""))
                    item["subtitles"] = find_matching_subtitles(item.get("id", ""), keyword)
                results.extend(data["data"]["items"])
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}
    
    results.sort(key=lambda x: x.get("datetime", ""), reverse=True)
    
    result_data = {
        "data": {
            "items": results,
            "pagination": {
                "page": page,
                "total_pages": 1,
                "total": len(results)
            }
        }
    }
    
    output_path = os.path.join(os.path.dirname(__file__), "search_result.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result_data, f, ensure_ascii=False, indent=2)
    
    return result_data