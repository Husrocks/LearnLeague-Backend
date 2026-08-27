import os
from groq import Groq

# Expecting GROQ_API_KEY in environment variables
client = Groq(api_key=os.environ.get("GROQ_API_KEY", "mock-key-for-dev"))

def generate_weekly_questions(user_topics: str) -> str:
    """
    Calls Groq LLM to generate technical interview questions based on the topics 
    the user studied during the week.
    """
    if os.environ.get("GROQ_API_KEY") == "mock-key-for-dev" or not os.environ.get("GROQ_API_KEY"):
        return f"Mock Question: Explain the core concepts of {user_topics} and how you would apply them in a production system."

    prompt = f"""
    You are an expert technical interviewer. The candidate has spent this week studying the following topics: 
    {user_topics}
    
    Generate 1 challenging, open-ended technical interview question to test their deep understanding of these topics. 
    Do not provide multiple choice. Ask a scenario-based question.
    Keep the response to exactly the question, no introductory text.
    """
    
    completion = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=256,
        top_p=1,
        stream=False,
    )
    
    return completion.choices[0].message.content

def evaluate_answer(question: str, user_answer: str) -> dict:
    """
    Evaluates the user's answer and returns a score and feedback.
    """
    if os.environ.get("GROQ_API_KEY") == "mock-key-for-dev" or not os.environ.get("GROQ_API_KEY"):
        return {
            "score": 85,
            "feedback": "Mock Feedback: Good attempt. You covered the basics, but missed some nuance on edge cases.",
            "follow_up": "What happens in a distributed system?"
        }

    prompt = f"""
    You are an expert technical interviewer evaluating a candidate's answer.
    
    Question asked: {question}
    Candidate's Answer: {user_answer}
    
    Evaluate the answer. Provide a JSON response exactly in this format, with no markdown formatting:
    {{
      "score": <0-100 integer score>,
      "feedback": "<1-2 sentence feedback>",
      "follow_up": "<1 follow-up question to probe deeper>"
    }}
    """
    
    completion = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=256,
        top_p=1,
        stream=False,
        response_format={"type": "json_object"}
    )
    
    import json
    try:
        result = json.loads(completion.choices[0].message.content)
        return result
    except:
        return {"score": 50, "feedback": "Failed to parse evaluation.", "follow_up": "Try again?"}
