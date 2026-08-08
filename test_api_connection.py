import urllib.request
import urllib.parse
import json
import time

BASE_URL = "http://127.0.0.1:8000/api"

def make_request(path, method="GET", data=None, token=None):
    url = f"{BASE_URL}{path}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Token {token}"
    
    req_data = json.dumps(data).encode('utf-8') if data else None
    req = urllib.request.Request(url, data=req_data, headers=headers, method=method)
    
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            res_data = response.read().decode('utf-8')
            res_json = json.loads(res_data) if res_data else {}
            cors_origin = response.headers.get("Access-Control-Allow-Origin")
            return {
                "status": response.status,
                "data": res_json,
                "cors_origin": cors_origin,
                "headers": dict(response.headers)
            }
    except urllib.error.HTTPError as e:
        err_data = e.read().decode('utf-8')
        try:
            err_json = json.loads(err_data)
        except:
            err_json = err_data
        return {
            "status": e.code,
            "error": err_json,
            "headers": dict(e.headers)
        }
    except Exception as e:
        return {
            "status": 0,
            "error": str(e),
            "headers": {}
        }

def test_api():
    print("--- 1. Testing CORS Preflight (OPTIONS Request) ---")
    req = urllib.request.Request(
        f"{BASE_URL}/auth/login/",
        method="OPTIONS",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type"
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as res:
            print("OPTIONS status:", res.status)
            print("CORS Origin Header:", res.headers.get("Access-Control-Allow-Origin"))
            print("CORS Allow Methods:", res.headers.get("Access-Control-Allow-Methods"))
    except Exception as e:
        print("CORS Preflight Failed:", e)

    email = f"test_{int(time.time())}@example.com"
    password = "password123"
    
    print(f"\n--- 2. Registering User: {email} ---")
    reg_res = make_request("/auth/register/", "POST", {"email": email, "password": password, "username": "test_agent_user"})
    print("Status:", reg_res.get("status"))
    print("Response:", json.dumps(reg_res.get("data"), indent=2))
    
    if reg_res.get("status") != 201:
        print("Registration failed, stopping test.")
        return
        
    token = reg_res["data"]["token"]
    
    print("\n--- 3. Logging in ---")
    login_res = make_request("/auth/login/", "POST", {"email": email, "password": password})
    print("Status:", login_res.get("status"))
    print("Token retrieved:", login_res.get("data", {}).get("token"))
    print("CORS Access-Control-Allow-Origin:", login_res.get("cors_origin"))
    
    print("\n--- 4. Fetching Current User (/me) ---")
    me_res = make_request("/auth/me/", "GET", token=token)
    print("Status:", me_res.get("status"))
    print("User Data:", json.dumps(me_res.get("data"), indent=2))
    
    print("\n--- 5. Adding a Link ---")
    link_data = {
        "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "video_id": "dQw4w9WgXcQ",
        "title": "Rick Astley - Never Gonna Give You Up",
        "author_name": "Rick Astley",
        "duration": "3:32",
        "category": "Music"
    }
    add_res = make_request("/links/", "POST", link_data, token=token)
    print("Status:", add_res.get("status"))
    print("Link Created:", json.dumps(add_res.get("data"), indent=2))
    
    if add_res.get("status") != 201:
        print("Adding link failed.")
        return
        
    link_id = add_res["data"]["id"]
    
    print("\n--- 6. Retrieving Links List ---")
    list_res = make_request("/links/", "GET", token=token)
    print("Status:", list_res.get("status"))
    print("Total Links in DB:", len(list_res.get("data", [])))

    print("\n--- 7. Updating (Liking) Link ---")
    update_res = make_request(f"/links/{link_id}/", "PATCH", {"liked": True}, token=token)
    print("Status:", update_res.get("status"))
    print("Liked state:", update_res.get("data", {}).get("liked"))

    print("\n--- 8. Deleting Link ---")
    del_res = make_request(f"/links/{link_id}/", "DELETE", token=token)
    print("Status:", del_res.get("status"))
    print("Deleted successfully:", del_res.get("data") == {"success": True})

if __name__ == "__main__":
    test_api()
