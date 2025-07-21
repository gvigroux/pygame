
import asyncio
import httpx

cacert_path = r"C:/Users/gvigroux/AppData/Local/Programs/Python/Python313/Lib/site-packages/certifi/cacert_thales.pem"


async def main():
    transport = httpx.AsyncHTTPTransport(verify=cacert_path)
    async with httpx.AsyncClient(transport=transport ) as client:
        r = await client.get("https://x.com")
        print(r.status_code)

asyncio.run(main())
