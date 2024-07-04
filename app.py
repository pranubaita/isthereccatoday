from flask import Flask, render_template, request, redirect, url_for, Response
from datetime import datetime
import json
import functools

app = Flask(__name__)

# Basic authentication credentials
USERNAME = 'admin'
PASSWORD = 'password'


# Load CCA schedule from a file
def load_schedule():
    try:
        with open('cca_schedule.json', 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return {}


# Save CCA schedule to a file
def save_schedule(schedule):
    with open('cca_schedule.json', 'w') as file:
        json.dump(schedule, file)


# Basic authentication decorator
def check_auth(username, password):
    return username == USERNAME and password == PASSWORD


def authenticate():
    return Response(
        'Could not verify your access level for that URL.\n'
        'You have to login with proper credentials', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'})


def requires_auth(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)

    return decorated


@app.route('/')
def home():
    current_date = datetime.now().strftime('%Y-%m-%d')
    cca_schedule = load_schedule()
    cca_info = cca_schedule.get(current_date, {"is_cca": False, "subject": "", "start_time": "", "end_time": ""})
    formatted_date = format_date(current_date)
    return render_template('index.html', current_date=formatted_date, cca_info=cca_info)


@app.route('/admin', methods=['GET', 'POST'])
@requires_auth
def admin():
    cca_schedule = load_schedule()
    if request.method == 'POST':
        edit_date = request.form['edit_date']
        date = request.form['date']
        subject = request.form['subject']
        start_time = request.form['start_time']
        end_time = request.form['end_time']
        is_cca = 'is_cca' in request.form
        cca_schedule[date] = {
            'is_cca': is_cca,
            'subject': subject,
            'start_time': start_time,
            'end_time': end_time
        }
        if edit_date and edit_date != date:
            cca_schedule.pop(edit_date, None)
        save_schedule(cca_schedule)
        return redirect(url_for('admin'))
    return render_template('admin.html', cca_schedule=cca_schedule)


@app.route('/delete/<date>', methods=['POST'])
@requires_auth
def delete(date):
    cca_schedule = load_schedule()
    if date in cca_schedule:
        del cca_schedule[date]
        save_schedule(cca_schedule)
    return redirect(url_for('admin'))


def format_date(date_str):
    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
    day = date_obj.day
    month = date_obj.strftime('%B')
    suffix = 'th' if 11 <= day <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')
    formatted_date = f"{day}{suffix} of {month}"
    return formatted_date


if __name__ == '__main__':
    app.run(debug=True)
