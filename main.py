from contextlib import asynccontextmanager
import datetime
from time import time
from fastapi import FastAPI, Depends , HTTPException, BackgroundTasks, Request
from pydantic import BaseModel
import asyncio
import login
from fastapi.middleware.cors import CORSMiddleware
import hashlib
from secure import encryptor
from database import session, engine
import models
import redis_task as redis
import send_mail
import preodic_checker
import os
from dotenv import load_dotenv
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
template = Jinja2Templates(directory="templates")
from sqlalchemy import text

models.base.metadata.create_all(bind=engine)
FRONT_END_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
origins = [
    "http://127.0.0.1:5173",
    "http://localhost:5173",
    FRONT_END_URL
]

def get_db():
    db = session()
    try:
        yield db
    finally:   
        db.close()


class LoginRequest(BaseModel):
    username: str
    password: str

class FetchClassRequest(BaseModel):
    username: str
    authToken: str
    jsessionid: str

class ReminderRequest(BaseModel):
    username: str
    courseType: str
    testType: str
    classSelect: str
    dateTime: str
    email: str
    authToken: str
    jsessionid: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.redis_pool = await redis.get_redis_connection()
    app.state.checker_task = asyncio.create_task(checker())
    app.state.keep_alive_task = asyncio.create_task(keep_alive_mail())
    yield
    await app.state.redis_pool.disconnect()
    app.state.checker_task.cancel()
    await app.state.checker_task
    app.state.keep_alive_task.cancel()
    await app.state.keep_alive_task

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def get_redis():
   
    if not hasattr(app.state, 'redis_pool'):
        raise HTTPException(status_code=500, detail="Redis connection pool not available")
    
   
    return redis.redis.Redis(connection_pool=app.state.redis_pool)

def update_token_db(username, auth_token, jsessionid, db):
    user = db.query(models.userDB).filter(models.userDB.username == username).first()
    if user:
        new_data = login.login(username, encryptor.decrypt(user.password))
        user.auth_token = new_data.get("auth_token")
        user.jsessionid = new_data.get("jsessionid")    
        db.commit()
        return new_data.get("auth_token"), new_data.get("jsessionid")
    return False

async def keep_alive_mail():
    while True:
        try: 
            load_dotenv()
            time_interval = int(os.getenv("KEEP_ALIVE_EMAIL_INTERVAL", 518400))
            admin_email = os.getenv("ADMIN_EMAIL")
            
            if not admin_email:
                print("ADMIN_EMAIL not configured, skipping keep-alive email")
                await asyncio.sleep(3600)  
                continue
            
            print(f"Sending keep-alive email to {admin_email} at {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            
            email_body = f"""
            <html>
            <body>
                <h2>Keep-Alive Email</h2>
                <p>This is an automated keep-alive email to ensure the email service is functioning properly.</p>
                
                <h3>System Status:</h3>
                <ul>
                    <li>Email Service: Working 👍</li>
                    <li>Timestamp: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</li>
                    <li>Next email in: {time_interval // 86400} days</li>
                </ul>
                
                <p><em>This email was sent automatically by the BBDC Reminder Service.</em></p>
            </body>
            </html>
            """
            
            success = send_mail.send_email_via_api(
                to_email=admin_email,
                subject="Keep-Alive Email - BBDC Reminder Service",
                html_body=email_body
            )

            if success.get("labelIds")[0] == "SENT":
                print(f"Keep-alive email sent successfully, sleeping for {time_interval} seconds ({time_interval // 86400} days)...")
            else:
                print("Failed to send keep-alive email")
                
            await asyncio.sleep(time_interval)
            
        except Exception as e:
            print(f"Error in keep-alive mail: {e}")
            await asyncio.sleep(time_interval/2)

async def checker():

    while True:
        try:
            load_dotenv()
            time_interval = int(os.getenv("PERIODIC_TASK_INTERVAL", 3600))
            print("Checking reminders at", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            
            await run_checker_cycle_async()
            print(f" Checker cycle completed, sleeping for {time_interval} seconds...")
            await asyncio.sleep(time_interval)

        except Exception as e:
            print(f"Error in checker: {e}")
            await asyncio.sleep(30)  

async def run_checker_cycle_async():

    try:

        db = session()        
        try:            
            reminders = await asyncio.get_event_loop().run_in_executor(
                None, lambda: db.query(models.reminderDB).all()
            )                        
            tasks = []
            for reminder in reminders:
                task = process_reminder_async(reminder, db)
                tasks.append(task)            
            
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
                        
        finally:            
            await asyncio.get_event_loop().run_in_executor(None, db.close)
            
    except Exception as e:
        print(f" Error in async checker cycle: {e}")

async def process_reminder_async(reminder, db):
    try:
        print(f"Checking reminder for: {reminder.username}")                
        user = await asyncio.get_event_loop().run_in_executor(
            None, lambda: db.query(models.userDB).filter(models.userDB.username == reminder.username).first()
        )
        
        if not user:
            print(f"User {reminder.username} not found, skipping...")
            return
        status = await asyncio.get_event_loop().run_in_executor(
            None, preodic_checker.check_slots, reminder, user
        )

        if status and status == {"error": "Token Expired"}:
            print(f"Token expired for {user.username}, refreshing...")
            new_tokens = await asyncio.get_event_loop().run_in_executor(
                None, update_token_db, user.username, None, None, db
            )
            if new_tokens:
                user.auth_token, user.jsessionid = new_tokens
                status = await asyncio.get_event_loop().run_in_executor(
                    None, preodic_checker.check_slots, reminder, user
                )
        
        if status and status.get("success"):
            print(f"Slot available for {reminder.email}!")
            # try:
            #     async with httpx.AsyncClient(timeout=10.0) as client:
            #         await client.post(
            #             "https://ntfy.sh/slot", 
            #             content=f"Reminder:{reminder.email} {reminder.classSelect} at {reminder.dateTime} is available! {status.get('message', '')}".encode('utf-8')
            #         )
            # except Exception as e:
            #     print(f"Failed to send notification: {e}")
            message = {
                "classSelect": reminder.classSelect,
                "dateTime": reminder.dateTime,
                "message": status.get("message", "")
            }

            await asyncio.get_event_loop().run_in_executor(
                None, send_mail.send_reminder_email, reminder.email, "BBDC Reminder", message
            ) 
            

            await asyncio.get_event_loop().run_in_executor(
                None, lambda: (db.delete(reminder), db.commit())
            )
                
    except Exception as e:
        print(f"Error processing reminder for {reminder.username}: {e}")


@app.get("/")
async def read_root():
    return {"Hello": "World"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}
    
@app.get("/keep-alive")
async def keep_alive(db=Depends(get_db)):
    response = db.execute(text("SELECT 1"))
    return {"status": response}

@app.post("/api/login")
async def first_login(login_request: LoginRequest, db: dict = Depends(get_db)):
    
    username = login_request.username
    password = login_request.password
    user = db.query(models.userDB).filter(models.userDB.username == username).first()
    if user:
        if password == encryptor.decrypt(user.password):
            return {"status": "success", "auth_token": user.auth_token, "jsessionid": user.jsessionid}
    else:
        data = login.login(username, password)
        if data.get("status") != "success":
            return {"status": data.get("status"), "error": "Login failed"}
        
        user_record = {
            "username": username,
            "password": encryptor.encrypt(password),
            "auth_token": data.get("auth_token"),
            "jsessionid": data.get("jsessionid")
        }
        db.add(models.userDB(**user_record))
        db.commit()
        return {"status": data.get("status"), "auth_token": data.get("auth_token"), "jsessionid": data.get("jsessionid")}
    
@app.post("/api/fetchClass/practical")
async def get_classes(fetch_request: FetchClassRequest, db=Depends(get_db)):
    data = login.practical_classes(fetch_request.authToken, fetch_request.jsessionid)
    if type(data) == dict and data == {"error": "Token Expired"}:
        updated = update_token_db(fetch_request.username, fetch_request.authToken, fetch_request.jsessionid, db)
        if updated:
            data = login.practical_classes(updated[0], updated[1])
    return data[0], data[1]
    return {"error": "Unable to fetch classes"}


# makes the reminder and adds to redis to get veriify the email later 
@app.post("/api/setreminder")
async def make_reminder(payload: ReminderRequest,  background_tasks: BackgroundTasks, db: dict = Depends(get_db), redis_connection=Depends(get_redis)):
    user = db.query(models.userDB).filter(models.userDB.username == payload.username).first()
    if not user:
        return {"status": "error", "message": "User not found"}

    if payload.authToken != user.auth_token or payload.jsessionid != user.jsessionid:
        return {"status": "error", "message": "Invalid auth token or jsessionid"}

    reminder_id = hashlib.sha256(f"{payload.username}{payload.classSelect}{payload.courseType}".encode()).hexdigest()
    existing_reminder = db.query(models.reminderDB).filter(models.reminderDB.id == reminder_id).first()
    if await redis_connection.exists(reminder_id):
        return {"status": "error", "message": "Reminder confirmation pending. Please check your email."}

    if existing_reminder:
        return {"status": "error", "message": "Reminder already exists"}

    reminder_record = {
        "id": reminder_id,
        "username": payload.username,
        "classSelect": payload.classSelect,
        "dateTime": payload.dateTime,
        "email": payload.email,
        "courseType": payload.courseType,
        "testType": payload.testType
    }
    

    success = await redis.add_task(redis_connection, reminder_record)

    background_tasks.add_task(send_mail.send_confirmation_email, payload.email, reminder_id)
    
    if success:
        return {"status": "success", "message": "Reminder set successfully"}
    else:
        return {"status": "error", "message": "Failed to set reminder"}

# endpoint to add the reminder to the database after email verification
@app.get("/api/setreminder/{reminder_id}", response_class=HTMLResponse)
async def set_reminder(reminder_id: str,request: Request, db: dict = Depends(get_db), redis_connection=Depends(get_redis)):
    print("Setting reminder with ID:", reminder_id)
    try:
        data = await redis.get_task(redis_connection, reminder_id)
        if data is None:
            return template.TemplateResponse("reminder_success.html", {
                "request": request,
                "status": "error",
                "message": "Reminder not found or verification link has expired",
                "frontend_url": FRONT_END_URL
            })
        db.add(models.reminderDB(**data))
        db.commit() 
        return template.TemplateResponse("reminder_success.html", {
            "request": request,
            "status": "success",
            "message": "Reminder confirmed and set successfully",
            "frontend_url": FRONT_END_URL
        })
        # return {"status": "success", "message": "Reminder confirmed and set successfully"}
    except Exception as e:
        print("Error occurred while setting reminder:", e)
        return template.TemplateResponse("reminder_success.html", {
            "request": request,
            "status": "error",
            "message": "An error occurred while setting the reminder",
            "frontend_url": f"{BACKEND_URL}/api/setreminder/{reminder_id}"
        })
