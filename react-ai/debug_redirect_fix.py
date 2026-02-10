import httpx
import asyncio
import logging
import sys

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
MAX_REDIRECT_HOPS = 20
REQUEST_TIMEOUT = 10.0

async def track_redirects(url: str):
    print(f"🔍 Analyzing: {url}")
    try:
        async with httpx.AsyncClient(
            follow_redirects=True,
            max_redirects=MAX_REDIRECT_HOPS + 1,
            timeout=REQUEST_TIMEOUT,
            verify=False,  # SSL 인증서 검증 무시
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "Accept-Language": "en-US,en;q=0.9,ko;q=0.8",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1"
            }
        ) as client:
            response = await client.get(url)
            print(f"✅ Status: {response.status_code}")
            print(f"🔗 URL: {response.url}")
            print(f"📄 History: {len(response.history)}")
            
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = "https://connectingmoment.com/"
    
    asyncio.run(track_redirects(url))
