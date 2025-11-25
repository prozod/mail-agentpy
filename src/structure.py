from pydantic import BaseModel, Field
from pydantic.types import conlist
from typing import Optional

class CalendarEvent(BaseModel):
    """calendar event extracted from an email (output)"""
    
    # using Field method so that we can provide the LLM accurate descriptions clearly (he a dumbo)
    title: str = Field(description="A concise summary or subject for the meeting.")
    date_time: str = Field(description="The full date and time of the event. Please analyze the sentences very carefully, as there might be dates and time overlapping in some messages (example: meeting date vs. the actual event date). I want you to extract the meeting date and time precisely, when we will meet to talk and discuss, rather than the event or trip date. Be aware of phrases such as '11 in the morning' meaning 11:00AM, or '4 in the afternoon' meaning 4:00PM. Do not mess up digits, '11' is eleven and '1' is one. Some dates might be specified as 24Hr clock, therefore 19:00 means 07:00PM. Analyze the whole message before taking a decision. Must be in ISO 8601 format (YYYY-MM-DDTHH:mm:ssZ) if possible, or plain English if date is ambiguous. Formatted for Google Calendar.")
    timezone: str = Field(description="The time-zone during which the event or meeting will happen, if it is mentioned. If it is not, default to GMT+2.")
    location: Optional[str] = Field(description="The physical location (address) or video conference link (e.g., Zoom/Meet URL, Discord, Microsoft Teams). If not present, use None.")
    summary: Optional[str] = Field(description="The summary of the event that is being mentioned. What is it about? A concise, one or two sentence summary.")
    attendees: conlist(str, min_length=1) = Field(description="A list of people mentioned who are expected to attend (or their email addresses).") # type: ignore (altfel imi plange Pylance)
    
class ExtractedCalendarInfo(BaseModel):
    """A list of calendar events found in the message."""
    events: conlist(CalendarEvent, min_length=0) = Field(description="A list of all distinct calendar events found in the message.") # type: ignore
