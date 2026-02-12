#!/usr/bin/env python3
"""
Feed Aggregator Skill
统一素材聚合器，从多个来源获取内容供 LLM 选择。
"""
import json
import random
import feedparser
from pathlib import Path
from core.utils_security import load_config, resolve_path

# 导入现有的 RSS Reader 作为 fallback
try:
    from skills.rss_reader import get_random_rss_item as get_fallback_rss_item
except ImportError:
    get_fallback_rss_item = lambda: None

SEC_CONFIG = load_config()

# Hacker News Feeds
HN_FEEDS = [
    "https://hnrss.org/frontpage?points=100",
    "https://hnrss.org/newest?points=200", 
    "https://hnrss.org/show?points=50",
]

def _get_twitter_briefing_item():
    """从 Twitter Briefing JSON 获取一条"""
    try:
        path = resolve_path("~/.openclaw/workspace/memory/twitter_briefing_data.json")
        if not path.exists():
            return None
            
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        tweets = data.get("tweets", [])
        if not tweets:
            return None
            
        # 优先取最近的 10 条随机选
        recent = tweets[:10]
        tweet = random.choice(recent)
        
        user = tweet.get('user')
        if not user:
            # 如果 user 为空，尝试使用 list source 作为标识
            list_source = tweet.get('source', 'Twitter')
            title = f"Post from {list_source}"
        else:
            title = f"@{user} on Twitter"

        return {
            "source": "Twitter Briefing",
            "title": title,
            "text": tweet.get("text", ""),
            "url": tweet.get("url", ""),
            "type": "social"
        }
    except Exception as e:
        print(f"⚠️ Error reading Twitter Briefing: {e}")
        return None

def _get_moltbook_item():
    """从 Moltbook JSON 获取一条"""
    try:
        path = resolve_path("~/.openclaw/workspace/memory/moltbook_data.json")
        if not path.exists():
            return None
            
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        posts = data.get("posts", [])
        if not posts:
            return None
            
        # 按 upvotes 排序，取 top 5 随机
        # 假设 posts 列表里的对象有 upvotes 字段，如果没有则默认 0
        sorted_posts = sorted(posts, key=lambda x: x.get("upvotes", 0), reverse=True)
        top_posts = sorted_posts[:5]
        post = random.choice(top_posts)
        
        return {
            "source": "Moltbook",
            "title": post.get("title", "Untitled"),
            "text": post.get("content", "")[:500],
            "url": post.get("url", ""),
            "type": "community"
        }
    except Exception as e:
        print(f"⚠️ Error reading Moltbook: {e}")
        return None

def _get_hackernews_item():
    """从 Hacker News RSS 获取一条"""
    try:
        feed_url = random.choice(HN_FEEDS)
        # Set timeout to prevent hanging
        feed = feedparser.parse(feed_url)
        
        if not feed.entries:
            return None
            
        # Random choice from top entries
        entry = random.choice(feed.entries[:10])
        
        return {
            "source": "Hacker News",
            "title": entry.get("title", ""),
            "text": entry.get("summary", "")[:500],
            "url": entry.get("link", ""),
            "type": "tech_news"
        }
    except Exception as e:
        print(f"⚠️ Error reading HN RSS: {e}")
        return None

def _get_fallback_item():
    """从现有 RSS Reader 获取一条"""
    try:
        item = get_fallback_rss_item()
        if not item:
            return None
            
        return {
            "source": item.get("source", "RSS"),
            "title": item.get("title", ""),
            "text": item.get("summary", "")[:500],
            "url": item.get("link", ""),
            "type": "tech_news"
        }
    except Exception as e:
        print(f"⚠️ Error reading fallback RSS: {e}")
        return None

def get_feed_item(preferred_source=None) -> dict | None:
    """
    获取一条素材。
    preferred_source: 'twitter', 'moltbook', 'hackernews', 'rss', None(随机)
    """
    sources = {
        'twitter': _get_twitter_briefing_item,
        'moltbook': _get_moltbook_item,
        'hackernews': _get_hackernews_item,
        'rss': _get_fallback_item
    }
    
    if preferred_source and preferred_source in sources:
        item = sources[preferred_source]()
        if item: return item

    # 如果没有指定或指定源失败，随机尝试
    # 权重调整：HN 和 Twitter 概率高一些
    choices = ['hackernews', 'twitter', 'moltbook', 'rss']
    random.shuffle(choices)
    
    for source in choices:
        item = sources[source]()
        if item: return item
        
    return None

def get_feed_items_batch(count=3) -> list[dict]:
    """获取多条不重复素材（用于 LLM 选择最有趣的一条）"""
    items = []
    seen_urls = set()
    
    # 尝试源的顺序
    source_functions = [
        _get_hackernews_item,
        _get_twitter_briefing_item,
        _get_moltbook_item,
        _get_fallback_item,
        # 重复一些源以增加获取几率
        _get_hackernews_item,
        _get_twitter_briefing_item
    ]
    random.shuffle(source_functions)
    
    for fetch_func in source_functions:
        if len(items) >= count:
            break
            
        try:
            item = fetch_func()
            if item and item.get('url') and item['url'] not in seen_urls:
                items.append(item)
                seen_urls.add(item['url'])
        except Exception:
            continue
            
    return items

if __name__ == "__main__":
    # Test
    print("--- Single Item ---")
    print(get_feed_item())
    print("\n--- Batch Items ---")
    batch = get_feed_items_batch(3)
    for i, item in enumerate(batch):
        print(f"{i+1}. [{item['source']}] {item['title']}")
