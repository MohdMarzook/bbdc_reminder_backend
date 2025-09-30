import datetime
import login


def check_slots(reminder,user):
    if reminder.testType == "practical":
        course_type = reminder.courseType  
        class_no = reminder.classSelect 
        data = login.practical_dates(course_type, class_no, user.auth_token, user.jsessionid, reminder.dateTime[:7].replace("-","")) 
        if data and data == {"error": "Token Expired"}:
            return data            
        if data:
            reminder_datetime = datetime.datetime.fromisoformat(reminder.dateTime)
            
            print(f"\n🔍 Looking for slots around: {reminder_datetime.strftime('%Y-%m-%d %H:%M')}")
            print("=" * 60)
            
            for slot in data.get("releasedSlotListGroupByDay").items():
                slot_date = slot[0] 
                slot_list = slot[1] 

                slot_date_clean = slot_date[:10]
                slot_date_obj = datetime.datetime.strptime(slot_date_clean, "%Y-%m-%d")
                
                date_diff = (slot_date_obj.date() - reminder_datetime.date()).days
                if date_diff == 0:
                    for count, slot in enumerate(slot_list):
                        if slot.get("bookingProgress") == "Available":
                            if reminder_datetime.time() == datetime.time(0, 0):
                                return {"success": True, "message": "found the the available slots in that day"}
                            else:
                                end_time = slot.get("endTime")      
                                start_time = slot.get("startTime")  

                            slot_start_datetime = datetime.datetime.strptime(
                                f"{slot_date_clean} {start_time}", "%Y-%m-%d %H:%M"
                            )
                            slot_end_datetime = datetime.datetime.strptime(
                                f"{slot_date_clean} {end_time}", "%Y-%m-%d %H:%M"
                            )

                            is_exact_match = (slot_start_datetime <= reminder_datetime <= slot_end_datetime)
                            if is_exact_match:
                                return {"success": True, "message": "found the the available slot for the exact time"}
    return None