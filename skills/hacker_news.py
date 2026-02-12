#!/usr/bin/env python3
"""
Hacker News Skill (RSS Version)
Fetches top stories from Hacker News via hnrss.org
"""
import feedparser
import random

HN_FEEDS = [
    "https://hnrss.org/frontpage?points=100",
    "https://hnrss.org/newest?points=200", 
    "https://hnrss.org/show?points=50",
]

def fetch_top_stories(limit=5):
    """通过 hnrss.org RSS 获取 HN 热门"""
    try:
        feed_url = random.choice(HN_FEEDS)
        # Set a timeout for feedparser (it uses urllib underneath)
        # But feedparser.parse doesn't accept timeout directly in all versions.
        # It's better to rely on system defaults or wrap it, but for simplicity here we just call it.
        feed = feedparser.parse(feed_url)
        
        if not feed.entries:
            return None
            
        entries = feed.entries[:limit]
        if not entries:
            return None
            
        entry = random.choice(entries)
        
        return {
            'source': 'Hacker News',
            'title': entry.get('title', ''),
            'url': entry.get('link', ''),
            'summary': entry.get('summary', '')[:500],
            'score': 0,  # hnrss doesn't always include score
            'type': 'tech_news'
        }
    except Exception as e:
        print(f"⚠️ Error fetching HN RSS: {e}")
        return None

if __name__ == "__main__":
    item = fetch_top_stories()
    if item:
        print(f"✅ [{item['source']}] {item['title']}\n{item['url']}")
    else:
        print("❌ No HN items found.")
