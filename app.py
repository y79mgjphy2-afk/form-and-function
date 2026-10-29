import json
import os
import secrets
import time
import urllib.request

from flask import Flask, jsonify, render_template, request, session

app = Flask(__name__)
app.secret_key = os.getenv('SESSION_SECRET') or secrets.token_hex(32)
app.config.update(MAX_CONTENT_LENGTH=8000, SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Strict')

GOALS = {'strength', 'general_fitness', 'weight_loss', 'mobility'}
EXPERIENCE = {'beginner', 'intermediate', 'advanced'}
EQUIPMENT = {'bodyweight', 'dumbbells', 'bands', 'gym'}


def demo_plan(goal, experience, days, equipment):
    exercises = {
        'strength': [
            [('Squat', '3', '8-10'), ('Push-up', '3', '6-12'), ('Glute bridge', '3', '10-15'), ('Dead bug', '2', '8 each side')],
            [('Hip hinge', '3', '8-10'), ('Row', '3', '8-12'), ('Reverse lunge', '3', '8 each side'), ('Plank', '3', '20-40 sec')],
            [('Split squat', '3', '8 each side'), ('Overhead press', '3', '8-10'), ('Bird dog', '2', '8 each side'), ('Calf raise', '3', '12-15')],
        ],
        'general_fitness': [
            [('Sit-to-stand squat', '3', '10-12'), ('Incline push-up', '3', '6-10'), ('March in place', '3', '30 sec'), ('Bird dog', '2', '8 each side')],
            [('Step-back lunge', '3', '8 each side'), ('Row', '3', '10-12'), ('Glute bridge', '3', '12'), ('Dead bug', '2', '8 each side')],
            [('Squat', '3', '10'), ('Wall push-up', '3', '10'), ('Hip hinge', '3', '10'), ('Easy brisk walk', '1', '10-15 min')],
        ],
        'weight_loss': [
            [('Squat', '3', '10-12'), ('Incline push-up', '3', '6-10'), ('Step-back lunge', '2', '8 each side'), ('Easy brisk walk', '1', '10-20 min')],
            [('Hip hinge', '3', '10'), ('Row', '3', '10-12'), ('March in place', '3', '30 sec'), ('Dead bug', '2', '8 each side')],
            [('Sit-to-stand squat', '3', '12'), ('Wall push-up', '3', '10'), ('Glute bridge', '3', '12'), ('Easy brisk walk', '1', '10-20 min')],
        ],
        'mobility': [
            [('Cat-cow', '2', '6 slow reps'), ('Hip hinge practice', '2', '8'), ('Wall slide', '2', '8'), ('Easy walk', '1', '10 min')],
            [('Open-book rotation', '2', '6 each side'), ('Ankle rocks', '2', '8 each side'), ('Glute bridge', '2', '10'), ('Easy walk', '1', '10 min')],
            [('Bird dog', '2', '6 each side'), ('Supported squat hold', '2', '20 sec'), ('Wall slide', '2', '8'), ('Easy walk', '1', '10 min')],
        ],
    }
    if equipment == 'bodyweight':
        replacements = {'Row': 'Prone W raise', 'Overhead press': 'Pike push-up or wall reach'}
    elif equipment == 'bands':
        replacements = {'Row': 'Band row', 'Overhead press': 'Band overhead press'}
    elif equipment == 'dumbbells':
        replacements = {'Row': 'Dumbbell row', 'Overhead press': 'Dumbbell overhead press', 'Squat': 'Dumbbell goblet squat'}
    else:
        replacements = {'Row': 'Cable or machine row', 'Squat': 'Goblet or machine squat', 'Overhead press': 'Dumbbell overhead press'}
    labels = ['Workout A', 'Workout B', 'Workout C']
    if experience == 'beginner':
        sets_factor = 1
    else:
        sets_factor = 1 if experience == 'intermediate' else 2
    workouts = []
    for index in range(days):
        movements = exercises[goal][index % len(exercises[goal])]
        workouts.append({
            'day': f'Day {index + 1}',
            'focus': labels[index % len(labels)],
            'exercises': [
                {'name': replacements.get(name, name), 'sets': str(int(sets) * sets_factor), 'reps': reps, 'rest': '60-90 sec'}
                for name, sets, reps in movements
            ],
        })
    return {
        'summary': f'A {days}-day {goal.replace("_", " ")} plan for a {experience} level, using {equipment}. Start easy and add effort gradually.',
        'workouts': workouts,
        'tips': [
            'Warm up gently for 5 minutes and use a comfortable range of motion.',
            'Rest at least one day between strength sessions when possible.',
            'Stop if you feel sharp pain, dizziness, or unusual shortness of breath.',
        ],
    }


def valid_plan(plan, days):
    if not isinstance(plan, dict) or not isinstance(plan.get('summary'), str) or not 1 <= len(plan['summary']) <= 800:
        return False
    if not isinstance(plan.get('workouts'), list) or len(plan['workouts']) != days:
        return False
    if not isinstance(plan.get('tips'), list) or not 1 <= len(plan['tips']) <= 8:
        return False
    if not all(isinstance(tip, str) and 1 <= len(tip) <= 300 for tip in plan['tips']):
        return False
    for workout in plan['workouts']:
        if not isinstance(workout, dict):
            return False
        if any(not isinstance(workout.get(key), str) or not 1 <= len(workout[key]) <= 100 for key in ('day', 'focus')):
            return False
        movements = workout.get('exercises')
        if not isinstance(movements, list) or not 2 <= len(movements) <= 8:
            return False
        for movement in movements:
            if not isinstance(movement, dict):
                return False
            if any(not isinstance(movement.get(key), str) or not 1 <= len(movement[key]) <= 100 for key in ('name', 'sets', 'reps', 'rest')):
                return False
    return True


def live_plan(profile):
    instructions = (
        'Act as a cautious general fitness planning assistant, not a medical professional. '
        'Create an achievable workout plan for the provided profile. Return only a JSON object with '
        'keys summary (string), workouts (array), and tips (array of strings). Each workout has day, '
        'focus, and exercises (2 to 8 objects). Each exercise has name, sets, reps, and rest (all strings). '
        'Create exactly the requested number of workouts. Keep beginner plans gentle and equipment-specific. '
        'Do not promise weight loss or prescribe extreme exercise, diets, or supplements. If limitations '
        'mention pain, injury, pregnancy, or a medical condition, do not prescribe exercise for that issue; '
        'recommend the person consult a qualified health professional before proceeding. Include a reminder '
        'to stop for sharp pain, dizziness, or unusual shortness of breath.'
    )
    payload = {
        'model': os.getenv('OPENAI_MODEL', 'gpt-4.1-mini'),
        'store': False,
        'instructions': instructions,
        'input': json.dumps(profile),
        'max_output_tokens': 2200,
    }
    req = urllib.request.Request(
        'https://api.openai.com/v1/responses',
        data=json.dumps(payload).encode(),
        headers={'Authorization': 'Bearer ' + os.environ['OPENAI_API_KEY'], 'Content-Type': 'application/json'},
    )
    with urllib.request.urlopen(req, timeout=45) as response:
        data = json.load(response)
    text = '\n'.join(
        part.get('text', '')
        for item in data.get('output', [])
        for part in item.get('content', [])
        if part.get('type') == 'output_text'
    )
    plan = json.loads(text)
    if not valid_plan(plan, profile['days']):
        raise ValueError('The AI response did not match the workout plan format.')
    return plan


@app.get('/')
def index():
    return render_template('index.html')


@app.get('/api/config')
def config():
    session.setdefault('csrf', secrets.token_hex(24))
    return jsonify(live=bool(os.getenv('OPENAI_API_KEY')), csrf=session['csrf'])


@app.before_request
def guard():
    if request.method == 'POST' and (
        not session.get('csrf')
        or not secrets.compare_digest(request.headers.get('X-CSRF-Token', ''), session['csrf'])
    ):
        return jsonify(error='Refresh the page before submitting.'), 403


@app.after_request
def headers(response):
    response.headers['Content-Security-Policy'] = "default-src 'self'; style-src 'self'; script-src 'self'; frame-ancestors 'none'; base-uri 'none'"
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Cache-Control'] = 'no-store'
    return response


@app.post('/api/plan')
def create_plan():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(error='Expected a JSON object.'), 400
    goal = data.get('goal')
    experience = data.get('experience')
    days = data.get('days')
    equipment = data.get('equipment')
    limitations = data.get('limitations', '')
    mode = data.get('mode')
    if (
        not isinstance(goal, str)
        or goal not in GOALS
        or not isinstance(experience, str)
        or experience not in EXPERIENCE
        or not isinstance(equipment, str)
        or equipment not in EQUIPMENT
    ):
        return jsonify(error='Choose a valid goal, experience level, and equipment option.'), 400
    if type(days) is not int or not 1 <= days <= 5:
        return jsonify(error='Choose 1 to 5 workout days per week.'), 400
    if not isinstance(limitations, str) or len(limitations) > 500:
        return jsonify(error='Keep notes about limitations under 500 characters.'), 400
    if mode not in ('demo', 'live'):
        return jsonify(error='Choose demo or live mode.'), 400
    if mode == 'live' and not os.getenv('OPENAI_API_KEY'):
        return jsonify(error='Configure OPENAI_API_KEY on the server first.'), 400
    if time.time() - session.get('last_plan', 0) < 3:
        return jsonify(error='Wait three seconds between plans.'), 429
    session['last_plan'] = time.time()
    profile = {
        'goal': goal,
        'experience': experience,
        'days': days,
        'equipment': equipment,
        'limitations': limitations.strip(),
    }
    if mode == 'demo':
        plan = demo_plan(goal, experience, days, equipment)
    else:
        try:
            plan = live_plan(profile)
        except Exception:
            app.logger.exception('Live fitness plan request failed')
            return jsonify(error='The live AI request failed. Check server connectivity, model access, and API configuration.'), 502
    return jsonify(plan=plan, mode=mode)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=int(os.getenv('PORT', '5000')), debug=False)
