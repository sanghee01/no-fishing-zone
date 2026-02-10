import httpx
import asyncio

async def test_access():
    url = "https://connectingmoment.com/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
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
    
    print(f"Testing access to {url}...")
    
    try:
        async with httpx.AsyncClient(verify=False, follow_redirects=True, timeout=10.0) as client:
            resp = await client.get(url, headers=headers)
            print(f"Status: {resp.status_code}")
            print(f"History: {resp.history}")
            print(f"Final URL: {resp.url}")
            if resp.status_code == 200:
                print("✅ Access Successful!")
            else:
                print("❌ Access Failed")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_access())
