from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String  

base = declarative_base()
class userDB(base):
    __tablename__ = "users"
    username = Column(String, primary_key=True, index=True)
    password = Column(String)
    auth_token = Column(String)
    jsessionid = Column(String)


class reminderDB(base):
    __tablename__ = "reminders"
    id = Column(String, primary_key=True, index=True)
    username = Column(String)
    courseType = Column(String)
    testType = Column(String)
    classSelect = Column(String)
    dateTime = Column(String)
    email = Column(String)