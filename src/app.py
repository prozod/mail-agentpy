import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
import structure 
import gmail
from datetime import datetime, timedelta

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=API_KEY)

SYSTEM_INSTRUCTIONS = """
You are an intelligent event and schedule planner. You have to do my appointments.
You extract structured event data from emails and return ONLY valid JSON that matches the Pydantic schema.
If information is missing, use None or an empty list.
Mention that no event was found.
Dates should be converted to ISO 8601 format when possible.
"""

def main():
    creds = None
    if os.path.exists("token.json"):
        creds = gmail.Credentials.from_authorized_user_file("token.json", gmail.SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(gmail.Request())
        else:
            flow = gmail.InstalledAppFlow.from_client_secrets_file("credentials.json", gmail.SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:
        service = gmail.build("gmail", "v1", credentials=creds)
        cal = gmail.build("calendar", "v3", credentials=creds)
        if service is None:
             raise ValueError("Error: 'service' object was not initialized, please authenticate first!")

        msg_id, email_details = gmail.get_latest_email(service)

        for email in gmail.start_polling(service):
            print("NEW EMAIL RECEIVED!")

            structured = client.models.generate_content(
                model="gemini-2.5-flash-lite",
                contents=[SYSTEM_INSTRUCTIONS, email["full_body"]],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=structure.ExtractedCalendarInfo,
                ),
            )

            data: structure.ExtractedCalendarInfo = structured.parsed

            print("------------ NEW EVENT ------------")
            print(data)
            if(len(data.events)>0):
              print(data.events[0].title)
              print(data.events[0].summary)
              print(data.events[0].date_time)
              print(data.events[0].timezone)
              print(data.events[0].location)
              print(data.events[0].attendees)
            print("------------------------------------") 

            if(len(data.events)>0):
              start_dt = datetime.fromisoformat(data.events[0].date_time.replace('Z', '+00:00'))
              end_dt = start_dt + timedelta(hours=1)

              start_time_str_final = start_dt.isoformat()
              end_time_str_final = end_dt.isoformat()

              event = {
                'summary': data.events[0].title,
                'location': data.events[0].location,
                'description': data.events[0].summary,
                'start': {
                    'dateTime': start_time_str_final,
                    'timeZone': data.events[0].timezone,
                    },
                'end': {
                    'dateTime': end_time_str_final,
                    'timeZone': data.events[0].timezone,
                },
                'attendees': data.events[0].attendees,
              }

              event = cal.events().insert(calendarId='primary', body=event).execute()
              print('-----> Calendar event created: %s' % (event.get('htmlLink')))


    except gmail.HttpError as error:
        # proper error handling required ofc
        print(f"An error occurred: {error}")

if __name__ == "__main__":
    main()
