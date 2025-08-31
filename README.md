29th August 2025:

Jiomart introduced a link which takes a query parameter (a phone number) and provides a webpage with a unique coupon code which can be used to get a discount of Rs 100 on grocery products. 

Link: https://relianceretail.com/jiomart/?jiocpn=<phonenumber>

People had the opportunity to basically generate a lot of coupon code with this link but like me they were busy ordering stuffs...

Some made 7-8 orders that day alone before 12pm when finally the coupon generator link showed the message "Happy hours have ended. Please check back tomorrow"

30th August 2025 (The inspection and awakening):

When the link expired, somewhere I knew that I lost a big opportunity to generate a lot of coupon code. A simple python script that orchestrates generating a 10 digit phone number, an api call, and a html parser to get the coupon codes. But it was too late.

However, I noticed a pattern that was there in the coupon code. Each one of them had digits and letters in an alternate sequence making the length of the coupon code a total of 10. The pattern was "DADADADADA" where D is a digit between 1-9 and A is an alphabet between A-Z. I inspected the network calls and found out that the status code was 400 when the coupon code was incorrect. I copied the curl of the api call and asked chatgpt to create me a python script that generates a random code, makes an api call to the apply coupon get endpoint and outputs the response in the console.

So the script was basically designed to impersonate an api call with the cookies and headers of my own account to simulate that the request was originating from a browser.

After running the script and checking the logs I found out that the status codes were 400 in two cases:
- coupon code was incorrect (status message: invalid coupon code!)
- a valid code was already applied to the cart (status message: cannot apply more than one coupon) 

The second case was interesting meaning that a valid code was already embedded in my cart with the random code that the script had generated and all the subsequent requests were basically getting rejected because a cart can have maximum one valid coupon applicable

So after running the script if i found out that the status messages like the second case were indefinitely being generated in the logs, I could be assured that a valid coupon code is already applied on my cart. AND IT WORKED. I was shocked to be honest because why would an api allow so many frequent requests to be handled in the first place. Maybe Jiomart developers had to roll out this feature immediately hence they couldnt focus on the rate limiting part.

NOW COMES THE OPTIMISATION:
I was now getting one coupon at a time (after 2-3 minutes). When I got the outcome I had to stop the script, then either use the valid coupon embedded in my cart to make an order, or note down the coupon code and remove the applied coupon by visiting my cart on the browser and then rerun the script again. This was inefficient and manual. So I rewrote the logic:

If status message is MAX_LIMIT_BREACHED (meaning a valid coupon was already embedded to my cart by the python script), fetch the coupon code thats present in my cart, use this code to unapply the coupon code from my cart with the unapply api and finally store this code in the final valid coupon code result list. Continue calling the apply coupon api.

apply_url = "https://www.jiomart.com/mst/rest/v1/5/cart/apply_coupon"
unapply_url = "https://www.jiomart.com/mst/rest/v1/5/cart/unapply_coupon?coupon_code=####&cart_id=649837557"
get_current_coupon_url = "https://www.jiomart.com/mst/rest/v1/5/cart/get"

All of these are GET apis

PROBLEMS I FACED:
- Only one thread was responsible for calling the apis which was really not utilising the CPU resources to the maximum. I then asked chatgpt to introduce multithreading to increase the throughput and execution speed.
- Occasionally I was also getting INVALID_CART_STATUS, SESSION_INVALID status messages. I noticed that the cart id, user id, auth codes and cookies of my account cart changed after a regular period of time. Maybe it was done by the devs to arrange the user activity more efficiently. To solve this I just had to go to my cart and inspect the network calls for the new cart id and user id. When the status was session invalid it meant that the authorization codes and cookies were incorrect so I had to get those and put the fresh cookies and headers in my python code to simulate the legit api calls again.
- On 30th August after generating lots of coupons, I found out that I was denied access to the jiomart website and was not able to call apis from my terminal. It turned out that, my PG router IP was blocked so I had to use a VPN and eventually change my internet connection to a different one (I used my roommates mobile internet ^_^ ). IT WORKED.
- I knew that eventually they will implement rate limiting on the api and the moment arrived on 31st August in the morning. The status code was 403 forbidden. I tried with multiple accounts as well. In the beginning it would be 400 bad request (indicating an invalid coupon code) and later it would become 403 forbidden error (indicating a rate limiting api forbidding frequent requests). I noticed that once you get a 403 forbidden you wont be able to apply a known valid coupon as well. All you will get is that "The coupon is invalid".


WHAT I COULD HAVE DONE BETTER:
- Implement an AI that would continuously analyse the valid coupons list and intelligently generate the random code that would increase the chances of a valid coupon.
- Create a dashboard with live updates on total no of api calls, category wise status codes with counts, valid codes etc
- Implement SQL injection attacks on the query parameters on the apply coupon api (although I tried it briefly on 30th August before submitting myself to greed and instant results)
- Endpoint discovery of the https://www.jiomart.com/mst/rest/v1 and https://www.jiomart.com/ sub-endpoints. Get an RCE or something.
- Reverse proxy using BurpSuite to modify requests and responses between the browser and the server (although I tried this on 31st August after finding out that brute-force was no longer the way to go. maybe a little more effort can help here)
- Instead of focussing on ordering stuff on 29th August, I should have focussed on creating an automation script to generate lots of coupon codes (not important as I could not have learnt much about bruteforce attacks if I already had what I needed)

WHAT I LEARNT:
- Multi-threading in Python
- 400 and 403 responses
- You should always rate limit your critical apis
- Logging only important stuffs
- Be aware of opportunistic possibilities
- Burp Suite (little bit)
- Dont screenrecord your brute-force

P.S. My account is barred from applying coupons anymore. Hope I dont get imprisoned :<(
