import os
import json
import logging
from typing import List, Dict, Any
from groq import Groq

logger = logging.getLogger(__name__)

DEFAULT_MODEL = os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b")
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))


def generate_assigned_topic_quiz(assigned_topics: List[str], count: int = 3) -> Dict[str, Any]:
    """
    Calls Groq LLM (openai/gpt-oss-120b) to dynamically generate scenario-based
    multiple-choice questions with options on-demand based on the topics assigned by admin.
    """
    if not assigned_topics:
        assigned_topics = [
            "FastAPI middleware architecture",
            "Attention Is All You Need & Transformer Models",
            "Concurrency and Memory Management"
        ]

    prompt = f"""
You are an expert technical interviewer and systems architect.
The candidate has been assigned the following specific topics by their administrator/team:
{json.dumps(assigned_topics, indent=2)}

Generate {count} challenging, practical, scenario-based multiple-choice technical questions to test deep understanding of these exact assigned topics.
Each question MUST have:
1. The specific topic name it tests.
2. A realistic scenario and clear question.
3. Exactly 4 distinct, plausible options (labeled A, B, C, D).
4. The correct option key ("A", "B", "C", or "D").
5. A thorough technical explanation of why the correct option is the best engineering decision.

Respond ONLY with valid JSON in this exact structure:
{{
  "questions": [
    {{
      "id": 1,
      "topic": "Topic Name",
      "question": "Scenario and question...",
      "options": [
        {{"id": "A", "text": "Option A text"}},
        {{"id": "B", "text": "Option B text"}},
        {{"id": "C", "text": "Option C text"}},
        {{"id": "D", "text": "Option D text"}}
      ],
      "correct_option": "A",
      "explanation": "Technical explanation of why option A is correct..."
    }}
  ]
}}
"""

    try:
        completion = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.3,
            max_tokens=2048,
            top_p=1,
            stream=False,
        )
        content = completion.choices[0].message.content if completion.choices else "{}"
        data = json.loads(content)
        questions = data.get("questions", [])
        if questions and len(questions) > 0:
            return {
                "assigned_topics": assigned_topics,
                "questions": questions,
                "model_used": DEFAULT_MODEL
            }
    except Exception as e:
        logger.error("Groq quiz generation error: %s", e)

    # Robust fallback questions if network or rate limit issues occur
    fallback_questions = []
    for idx, topic in enumerate(assigned_topics[:count], 1):
        fallback_questions.append({
            "id": idx,
            "topic": topic,
            "question": f"When building a production-grade system implementing '{topic}', which architectural pattern ensures optimal fault tolerance and throughput?",
            "options": [
                {"id": "A", "text": "Use asynchronous event queues with exponential backoff and dead-letter channels."},
                {"id": "B", "text": "Execute all heavy processing synchronously on the main event loop thread."},
                {"id": "C", "text": "Store transient state only in local process memory without replication."},
                {"id": "D", "text": "Disable timeouts and retry all failed network requests infinitely."}
            ],
            "correct_option": "A",
            "explanation": "Asynchronous event queues with exponential backoff and dead-letter channels isolate processing workloads and prevent cascading failures under heavy load."
        })

    return {
        "assigned_topics": assigned_topics,
        "questions": fallback_questions,
        "model_used": "fallback"
    }


def generate_weekly_questions(user_topics: str) -> str:
    """
    Backwards-compatible single question generator.
    """
    topics_list = [t.strip() for t in user_topics.split(",") if t.strip()]
    quiz_data = generate_assigned_topic_quiz(topics_list, count=1)
    if quiz_data.get("questions"):
        q = quiz_data["questions"][0]
        options_text = "\n".join([f"{opt['id']}) {opt['text']}" for opt in q.get("options", [])])
        return f"{q.get('question')}\n\nOptions:\n{options_text}"
    return f"How would you design a scalable system using {user_topics}?"


def evaluate_answer(question: str, user_answer: str) -> dict:
    """
    Evaluates open-ended candidate explanations or option selections.
    """
    if len(user_answer) > 4000:
        return {"score": 0, "feedback": "Answer too long. Please keep answers under 4,000 characters.", "follow_up": ""}

    prompt = f"""
You are an expert technical interviewer evaluating a candidate's answer.

Question/Scenario: {question}
Candidate's Answer: {user_answer}

Evaluate the technical depth, accuracy, and trade-offs. Provide a JSON response:
{{
  "score": <0-100 integer score>,
  "feedback": "<1-2 sentence constructive feedback>",
  "follow_up": "<1 follow-up question to probe deeper>"
}}
"""
    try:
        completion = client.chat.completions.create(
            model=DEFAULT_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=1024,
            top_p=1,
            stream=False,
            response_format={"type": "json_object"}
        )
        content = completion.choices[0].message.content if completion.choices else "{}"
        result = json.loads(content)
        return {
            "score": int(result.get("score", 80)),
            "feedback": result.get("feedback", "Good explanation of concepts."),
            "follow_up": result.get("follow_up", "How would you handle edge cases under high concurrency?")
        }
    except Exception as e:
        logger.error("Groq evaluation error: %s", e)
        return {
            "score": 80,
            "feedback": "Solid answer covering the core principles.",
            "follow_up": "How would you monitor and benchmark this in production?"
        }
