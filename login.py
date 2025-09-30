import time
import requests
import capcha_solver
import datetime

def get_captcha():

    captcha_url = "https://booking.bbdc.sg/bbdc-back-service/api/auth/getLoginCaptchaImage"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:142.0) Gecko/20100101 Firefox/142.0",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.5",
        "Content-Type": "application/json",
        "JSESSIONID": "",
        "Sec-GPC": "1",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin"
    }
    response = requests.post(captcha_url, headers=headers)

    if response.status_code == 200:
        return response.json().get("data")      # Assuming the response contains JSON data
    else:
        return None
    

def submit_captcha(username, password, captcha_token, captcha_verify_code, captcha):
    url = "https://booking.bbdc.sg/bbdc-back-service/api/auth/login"
    payload = {
        "captchaToken": captcha_token,
        "userId": username,
        "userPass": password,
        "verifyCodeId": captcha_verify_code,
        "verifyCodeValue": captcha
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:142.0) Gecko/20100101 Firefox/142.0",
        "Accept": "application/json",
        "Connection": "keep-alive",
        "Accept-Language": "en-US,en;q=0.5",
        "Content-Type": "application/json",
        "JSESSIONID": "",
        "Sec-GPC": "1",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
        "Priority": "u=0"
    }

    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code == 200:
        return response.json()  # Assuming the response contains JSON data
    else:
        return None
    
def get_jsessionid(auth_token):
    url= "https://booking.bbdc.sg/bbdc-back-service/api/account/listAccountCourseType"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:142.0) Gecko/20100101 Firefox/142.0",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.5",
        "Content-Type": "application/json",
        "Authorization": auth_token,
        "JSESSIONID": "",
        "Sec-GPC": "1",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin"
    }
    response = requests.post(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        return None

def get_user_profile(auth_token, jsessionid):
    count = 0
    while count < 5:
        url = "https://booking.bbdc.sg/bbdc-back-service/api/account/getUserProfile"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:142.0) Gecko/20100101 Firefox/142.0",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.5",
            "Content-Type": "application/json",
            "Authorization": auth_token,
            "JSESSIONID": jsessionid,
            "Sec-GPC": "1",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin"
        }
        response = requests.post(url, headers=headers)

        if response.status_code == 200:
            return response.json()
        time.sleep(1)
        count += 1
    return None
    
def practical_tests(user_course, auth_token, jsessionid):
    url = "https://booking.bbdc.sg/bbdc-back-service/api/booking/c2practical/listPracticalTrainings"
    payload = {
        "courseType": user_course,
        "pageNo": 1,
        "pageSize": 10,
        "courseSubType": "Practical"
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:142.0) Gecko/20100101 Firefox/142.0",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.5",
        "Content-Type": "application/json",
        "Authorization": auth_token,
        "JSESSIONID": jsessionid,
        "Sec-GPC": "1",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin"
    }

    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code == 200:
        return response.json().get("data")  # Assuming the response contains JSON data
    else:
        return {"error": "Request failed", "status_code": response.status_code}

def login(username, password):
    auth_token = None
    while True:
        image_data = get_captcha()
        captcha_token = image_data.get("captchaToken")
        captcha_verify_code = image_data.get("verifyCodeId")
        captcha = capcha_solver.solve_captcha(image_data.get("image"))
        if captcha is None or len(captcha) != 5:
            continue
        auth_token = submit_captcha(username, password, captcha_token, captcha_verify_code, captcha).get("data").get("tokenContent")
        if auth_token is not None:
            break
    jsessionid = get_jsessionid(auth_token).get("data").get("activeCourseList")[0].get("authToken")
    print("login successful")
    return { "status": "success", "auth_token": auth_token, "jsessionid": jsessionid }

def practical_classes(auth_token, jsessionid):
    profile_data = get_user_profile(auth_token, jsessionid)
    if profile_data.get("code") == 402:
        return {"error": "Token Expired"}
    else:
        user_course = profile_data.get("data").get("enrolDetail").get("courseType")
    url = "https://booking.bbdc.sg/bbdc-back-service/api/booking/c2practical/listPracticalTrainings"
    payload = {
        "courseType": user_course,
        "pageNo": 1,
        "pageSize": 10,
        "courseSubType": "Practical"
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:142.0) Gecko/20100101 Firefox/142.0",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.5",
        "Content-Type": "application/json",
        "Authorization": auth_token,
        "JSESSIONID": jsessionid,
        "Sec-GPC": "1",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin"
    }

    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code == 200:
        bookable_classes = []
        classes = response.json().get("data").get("practicalTrainings")  # Assuming the response contains JSON data
        for x in classes:
            if x.get("canDoBooking"):
                bookable_classes.append(x.get("subStageSubNo"))
        
        
        return bookable_classes, user_course
    else:
        return {"error": "Request failed", "status_code": response.status_code}

def practical_dates(course_type, class_no , auth_token, jsessionid, slot_month=datetime.date.today().strftime("%Y%m")):
    url = "https://booking.bbdc.sg/bbdc-back-service/api/booking/c2practical/listPracSlotReleased"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:142.0) Gecko/20100101 Firefox/142.0",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.5",
        "Content-Type": "application/json",
        "Authorization": auth_token,
        "JSESSIONID": jsessionid,
        "Sec-GPC": "1",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin"
    }
    payload = {
        "courseType": course_type,
        #            2A
        "stageSubNo": class_no,
        # "stageSubNo":"1.01"
        "releasedSlotMonth":slot_month
    }   
    response = requests.post(url, json=payload, headers=headers)
    data = response.json()
    if response.status_code == 200:
        if data and data.get("code") == 402:
            return {"error": "Token Expired"}
        return data.get("data")  # Assuming the response contains JSON data
    else:
        return {"error": "Request failed", "status_code": response.status_code}


        
