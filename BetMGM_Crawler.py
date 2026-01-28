import asyncio
import json
import re
import csv
import os
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from collections import defaultdict
from urllib.parse import urljoin, urlparse


class SportsbookLinkScraper:    
    
    BETTING_URL_PATTERNS = [ 
        r'/event/[\w-]+',
        r'/game/[\w-]+',
        r'/match/[\w-]+',
        r'/markets/\d+',
        r'/fixtures/\d+',
        r'/competitions/[\w-]+',
        
        
        r'/(nba|nfl|mlb|nhl|ncaab|ncaaf)/[\w-]+/[\w-]+',
        r'/(soccer|football|basketball|baseball|hockey|tennis|mma|ufc|boxing)/[\w-]+/[\w-]+',
        
    
        r'/\d{4}/\d{2}/\d{2}/',
        r'/\d{4}-\d{2}-\d{2}/',
        
        r'/sports/[\w-]+/betting/',
        r'/en/sports/[\w-]+',
        
        r'/sportsbook/[\w-]+',
        
        
        r'/odds/[\w-]+',
        r'/lines/[\w-]+',
        r'/betting/[\w-]+',
    ]
    
    SKIP_PATTERNS = [
        r'/(login|register|account|profile|settings)',
        r'/(help|support|about|contact|careers|press)',
        r'/(terms|privacy|responsible|legal)',
        r'/(promotions|bonus|rewards|offers)',
        r'\.(css|js|json|xml|jpg|jpeg|png|gif|svg|ico|woff|woff2|ttf|eot)',
        r'/(api|cdn|static|assets|images|fonts)/',
        r'#',
        r'javascript:',
        r'mailto:',
        r'tel:',
    ]
    
    @classmethod
    def is_betting_link(cls, url):
        if not url or not isinstance(url, str):
            return False
            
        url_lower = url.lower()
        
        for pattern in cls.SKIP_PATTERNS:
            if re.search(pattern, url_lower):
                return False
        
        for pattern in cls.BETTING_URL_PATTERNS:
            if re.search(pattern, url_lower):
                return True
        
        sports = ['nba', 'nfl', 'mlb', 'nhl', 'soccer', 'football', 'basketball', 
                  'baseball', 'hockey', 'tennis', 'mma', 'ufc', 'boxing']
        has_sport = any(sport in url_lower for sport in sports)
        path_segments = len([p for p in urlparse(url_lower).path.split('/') if p])
        if has_sport and path_segments >= 3:
            return True
        
        return False


async def scrape_sportsbook_fast(
    start_url,
    max_pages=50,
    max_concurrent=10,
    verbose=True
):

    
    if verbose:
        print(f"\n{'='*80}")
        print(f"FAST SCRAPING: {start_url}")
        print(f"Concurrency: {max_concurrent} | Max pages: {max_pages}")
        print(f"{'='*80}\n")
    
    browser_config = BrowserConfig(
        browser_type="chromium",
        headless=True,
        viewport_width=1920,
        viewport_height=1080,
        java_script_enabled=True,
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    
    run_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        page_timeout=20000,
        wait_for="css:body",
        delay_before_return_html=1,
        exclude_external_links=False,
        word_count_threshold=5,
        excluded_tags=["script", "style", "svg"],
 q       js_code=[
            "window.scrollTo(0, document.body.scrollHeight / 2);",
            "await new Promise(r => setTimeout(r, 500));",
        ],
    )
    
    betting_links = []
    visited = set()
    to_visit = [start_url]
    base_domain = urlparse(start_url).netloc
    
    async with AsyncWebCrawler(config=browser_config) as crawler:
        
        while to_visit and len(visited) < max_pages:
            batch = []
            while to_visit and len(batch) < max_concurrent: 
                url = to_visit.pop(0)
                if url not in visited:
                    batch.append(url)
                    visited.add(url)
            
            if not batch:
                break
            
            if verbose:
                print(f"Processing batch of {len(batch)} URLs (visited: {len(visited)}/{max_pages})")
            
            tasks = [crawler.arun(url=url, config=run_config) for url in batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for url, result in zip(batch, results):
                if isinstance(result, Exception):
                    if verbose:
                        print(f"  Error on {url[:60]}: {str(result)[:50]}")
                    continue
                
                if not result.success:
                    continue
                
                
                found_urls = set()
                
                
                if hasattr(result, 'links') and result.links:
                    if hasattr(result.links, 'internal'):
                        for link in result.links.internal:
                            href = link.get('href', '')
                            if href:
                                found_urls.add(href)
                    if hasattr(result.links, 'external'):
                        for link in result.links.external:
                            href = link.get('href', '')
                            if href and base_domain in href:
                                found_urls.add(href)
                
                
                if result.html:
                    for match in re.finditer(r'href=["\']([^"\']+)["\']', result.html):
                        link_url = match.group(1)
                        if link_url.startswith(('http://', 'https://')):
                            if base_domain in link_url:
                                found_urls.add(link_url)
                        elif link_url.startswith('/'):
                            full_url = urljoin(url, link_url)
                            found_urls.add(full_url)
                
                new_betting = 0
                for found_url in found_urls:
                    found_url = found_url.split('#')[0].split('?')[0]
                    
                    if not found_url or found_url in visited:
                        continue
                    
                    
                    if urlparse(found_url).netloc != base_domain:
                        continue
                    
                    if SportsbookLinkScraper.is_betting_link(found_url):
                        if found_url not in [b['url'] for b in betting_links]:
                            betting_links.append({
                                'url': found_url,
                                'found_on': url
                            })
                            new_betting += 1
                        
                        if found_url not in visited and found_url not in to_visit:
                            to_visit.append(found_url)
                
                if verbose and new_betting > 0:
                    print(f"  {url[:60]}: +{new_betting} links (total: {len(betting_links)})")
    
    if verbose:
        print(f"\n{'='*80}")
        print(f"COMPLETE - Visited {len(visited)} pages, found {len(betting_links)} betting links")
        print(f"{'='*80}\n")
    
    return betting_links


def save_to_csv(betting_links, filename='betting_links.csv'):
    print(f"\n{'='*80}")
    print(f"FOUND {len(betting_links)} BETTING LINKS")
    print(f"{'='*80}\n")
    
    if not betting_links:
        print("No betting links found!\n")
        return
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    
    links_dir = os.path.join(parent_dir, 'Links')
    json_dir = os.path.join(parent_dir, 'JSON_Files')
    
    os.makedirs(links_dir, exist_ok=True)
    os.makedirs(json_dir, exist_ok=True)
    
    csv_path = os.path.join(links_dir, filename)
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['url'])
        for link in betting_links:
            writer.writerow([link['url']])
    
    print(f"Saved {len(betting_links)} links to: {csv_path}")
    
    json_filename = filename.replace('.csv', '.json')
    json_path = os.path.join(json_dir, json_filename)
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(betting_links, f, indent=2, ensure_ascii=False)
    
    print(f"Full data saved to: {json_path}\n")
    
    print("Preview of links:")
    print("-" * 80)
    for i, link in enumerate(betting_links[:10], 1):
        print(f"{i}. {link['url']}")
    
    if len(betting_links) > 10:
        print(f"\n... and {len(betting_links) - 10} more links")
    print()


async def main():
    
    
    print("\nSPORTSBOOK LINK SCRAPER")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    odds_dir = os.path.join(parent_dir, 'Odds')
    odds_file = os.path.join(odds_dir, 'betmgm_nba.csv')
    
    if os.path.exists(odds_file):
        os.remove(odds_file)
        print(f"Cleared odds file: {odds_file}")
    
    
    start_url = "https://www.in.betmgm.com/en/sports"
    
    
    print(f"Target: {start_url}\n")
    
    betting_links = await scrape_sportsbook_fast(
        start_url=start_url,
        max_pages=50,
        max_concurrent=10,
        verbose=True
    )
    
    save_to_csv(betting_links, filename='betting_links_betmgm.csv')


if __name__ == "__main__":
    asyncio.run(main())