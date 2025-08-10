from google.adk.agents.llm_agent import Agent
from pydantic import BaseModel, Field
from dotenv import load_dotenv
load_dotenv()

class EmailContent(BaseModel):
    subject: str = Field(..., description="The subject of the email")
    body: str = Field(..., description="The body content of the email")
    recipient: str = Field(..., description="The recipient's email address")

root_agent = Agent(
    model='gemini-2.0-flash',
    name='email_agent',
    description='An email agent that can write emails based on user input',
    instruction="""
    
    Please provide the subject, body, and recipient for the email.
    The email should be well-structured and professional.
    If you need to ask for more information, do so in a clear and concise manner.
    Important: your response should be a JSON object with the keys 'subject', 'body', and 'recipient'.
    Example:
    {
        "subject": "Meeting Request",
        "body": "I would like to schedule a meeting to discuss our project updates.",
        "recipient": "example@example.com"
    }
    If you don't have enough information, ask the user for more details.
    
    """,
    output_schema=EmailContent,
    output_key='email',
)
