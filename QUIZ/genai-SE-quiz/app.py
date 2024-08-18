from flask import Flask, render_template, request, redirect, url_for, session
from flask_session import Session
import random
import re
import os
from groq import Groq

app = Flask(__name__)
app.secret_key = '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'

# Configure Flask-Session
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

os.environ["GROQ_API_KEY"] = "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"

groq_client = Groq(
    api_key=os.environ.get("GROQ_API_KEY"),
)

topics = [
    "scenario based social media scam",
    "scenario based social media instagram scam",
    "scenario based facebook scam",
    "scenario based twitter scam",
    "scenario based instagram advertisement scam",
    "scenario based socialmedia scam",
    "scenario based social media advertisement scam",
    "Social Engineering using Social Media and Public Information",
    "scenario based facebook advertisement scam",
    "scenario based website advertisement scam"
    "scenario based Scams on Social Media",
    "scenario based Impersonation and Fake Accounts",
    "scenario based love Scams",
    "Scanario based social media pornography scams",
    "scanario based social media Catfishing",
    "scanario based social media Clickbait and Fake News",
    "scanario based social media Investment Scams",
    "Scenario based social media Prize and Lottery Scams",
    "scenario based social media Job Offer Scams",
    "scenario based social media Charity Scams",
    "scenario based social media survey Scams",
    "scenario based social media tech support Scams",
    "scenario based social credential harvesting Scams",
    "scenario based social media account hijacking Scams",
    "scenario based social media challenge Scams",
    "scenario based social media influencer Scams",
    "scenario based social media friend in need Scams"
]

def generate_question(model, temperature, top_p):
    topic = random.choice(topics)

    messages = [
        {
            "role": "system",
            "content": "You are an expert cybersecurity assistant that does not generate repeated content."
        },
        {
            "role": "user",
            "content": f"Create a unique multiple-choice question about {topic}. Provide the correct answer and three distractors. DONT REPEAT QUESTION"
        }
    ]

    try:
        response = groq_client.chat.completions.create(
            messages=messages,
            model=model,
            temperature=temperature,
            top_p=top_p
        )
        question = response.choices[0].message.content.strip()
        return question
    except Exception as e:
        print(f"Error generating question: {e}")
        return "Could not generate question at this time."

def parse_question(question_text):
    """Parses the generated question text into its components."""
    pattern = r"Question:\s*(.*?)\n\*\*A\)\*\*\s*(.*?)\n\*\*B\)\*\*\s*(.*?)\n\*\*C\)\*\*\s*(.*?)\n\*\*D\)\*\*\s*(.*?)\n\*\*Correct Answer:\*\*\s*([A-D])"
    match = re.search(pattern, question_text, re.DOTALL)

    if not match:
        return None

    question = match.group(1).strip()
    options = [match.group(i).strip() for i in range(2, 6)]
    correct_answer_letter = match.group(6).strip()
    correct_answer_index = ord(correct_answer_letter) - ord('A')  # Convert letter to index (A=0, B=1, C=2, D=3)

    return {
        "question": question,
        "options": options,
        "correct_answer": correct_answer_index
    }

@app.route('/')
def index():
    session['current_question'] = 0
    session['score'] = 0
    session['answers'] = []  # List of tuples: (question, user_answer, correct_answer)
    session['questions'] = []  # Clear previous questions
    return render_template('index.html')

@app.route('/question', methods=['GET', 'POST'])
def question():
    if request.method == 'POST' and session['current_question'] == 0:
        # Initialize model, temperature, and top-p for the first question
        session['model'] = request.form.get('model', 'llama-3.1-8b-instant')
        session['temperature'] = float(request.form.get('temperature', 0.8))
        session['top_p'] = float(request.form.get('top_p', 1))

    if request.method == 'POST':
        selected_choice = request.form.get('choice')
        current_question = session['current_question']

        # Check if the session already contains a question
        if current_question < len(session['questions']):
            correct_option = session['questions'][current_question]['correct_answer']

            if selected_choice is not None:
                selected_choice_index = int(selected_choice)
                
                # Store the question, user's answer, and the correct answer
                session['answers'].append({
                    "question": session['questions'][current_question]['question'],
                    "options": session['questions'][current_question]['options'],
                    "user_answer": selected_choice_index,
                    "correct_answer": correct_option
                })

                if selected_choice_index == correct_option:
                    session['score'] += 1

            # Increment the current question number after processing the answer
            session['current_question'] += 1
            if session['current_question'] >= 25:
                return redirect(url_for('result'))

    # Generate a new question only if we haven't hit the 25-question limit
    if session['current_question'] < 25:
        if len(session['questions']) <= session['current_question']:
            question_text = generate_question(session['model'], session['temperature'], session['top_p'])
            parsed_question = parse_question(question_text)
            while not parsed_question:  # Keep trying until a valid question is generated
                question_text = generate_question(session['model'], session['temperature'], session['top_p'])
                parsed_question = parse_question(question_text)

            # Store the parsed question
            session['questions'].append(parsed_question)

    is_last_question = (session['current_question'] == 24)
    return render_template(
        'question.html',
        question=session['questions'][session['current_question']],
        question_number=session['current_question'] + 1,
        is_last_question=is_last_question
    )

@app.route('/result')
def result():
    score = session['score']
    total_questions = 25
    passing_score = 0.70 * total_questions
    passed = score >= passing_score
    return render_template('result.html', score=score, total_questions=total_questions, passed=passed, answers=session['answers'])

if __name__ == '__main__':
    app.run(debug=True)
