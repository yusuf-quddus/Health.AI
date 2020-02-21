# importing general extensions of flask here
from flask import Flask, session, render_template, request, flash, url_for, redirect
import matplotlib.pyplot as plt
import flask
import app_functions
import pandas as pd
import os
import numpy as np
import seaborn as sns; sns.set()

from sklearn.linear_model import LogisticRegression

# The code for setting up a user session in flask and securing it with a secret_key is already installed below.
# You can jump directly to building your functions, and collecting HTML inputs for processing.

app = Flask(__name__)
app.config.from_object(__name__)
app.config['DEBUG'] = True
app.config["SECRET_KEY"] = app_functions.random_id(50)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":

        database = pd.read_csv('database.csv')
        session['email'] = request.form["email"]
        session['password'] = request.form["password"]

        if session['email'] in list(database['emails']):
            index = list(database['emails']).index(session['email'])

            if session['password'] == list(database['passwords'])[index]:
                session['name'] = database['name'][index]
                session['bmi'] = str(database['bmi'][index])
                return redirect(url_for('health'))

            else:
                flash('Incorrect username or password', 'error')
        else:
            flash('Incorrect username or password', 'error')

    return render_template('login.html')

@app.route("/about", methods=["GET", "POST"])
def about():
    return render_template('about.html')

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form["name"]
        bmi = request.form['bmi']
        email = request.form["email"]
        password = request.form["password"]
        password2 = request.form["password2"]

        if password != password2:
            flash('The passwords dont match. Please try again.', 'error')
        else:
            database = pd.read_csv('database.csv')

            if email in list(database['emails']):
                flash('An Account with the same email exists.', 'error')
            else:
                database.loc[len(database)] = [email, password, name, bmi]
                database.to_csv('database.csv', index=False)
                flash('Your Account has been successfuly created. You may log in now.', 'success')
                return(redirect(url_for('login')))

    return render_template('sign_up.html')

@app.route("/health", methods=["GET", "POST"])
def health():
    if 'name' not in session:
        flash('You are not logged in. Please log in first.', 'error')
        return redirect(url_for('login'))

    file = pd.read_csv('train.csv')
    file2 = pd.read_csv('step_and_calorie.csv')
    file_p = pd.read_csv('predicted_values.csv')
    final_index = 55

    cwd = os.getcwd()

    plt.figure(figsize=(12,6))
    plt.plot(file['time2'][0:final_index]-946.9, file['heart_rate'][0:final_index], color='blue', label= 'Original Values')
    plt.plot(file_p['time1']-947.31, file_p['t'], color='green', label='Predicted Values')
    plt.ylabel('Heart Rate', fontsize=20)
    plt.xlabel('Time', fontsize=20)
    plt.title('Variation of the Heart Rate with time', fontsize=30)
    plt.axhline(120, color='red')
    plt.axhline(80, color='red')
    plt.legend()
    plt.savefig(cwd+'/static/images/heart_rate.png')

    plt.figure(figsize=(20,10))
    plt.bar(np.array(file2['timediff2'])-947,file2['caloriesfood'], color='blue')
    plt.plot(np.array(file2['timediff2'])-947,file2['caloriesfood'], color='red')
    plt.title('Daily Calorie Intake', fontsize=40)
    plt.xlabel('Time', fontsize=30)
    plt.ylabel('Calories', fontsize=30)
    plt.savefig(cwd + '/static/images/calories.png')

    plt.figure(figsize=(20,10))
    plt.plot(np.array(file2['timediff2'])-947,file2['step_counttotal'], color='blue')
    plt.title('Variation of step counts over time', fontsize=40)
    plt.xlabel('Time', fontsize=30)
    plt.ylabel('Step Counts', fontsize=30)
    plt.savefig(cwd + '/static/images/step_count.png')

    session['heart_alerts'] = []
    session['calorie_alerts'] = []

    for i in range(33):
        difference = file['heart_rate'][i] - file_p['t'][i]
        if abs(difference) > 20:
            alert = dict()

            if abs(difference) > 30:
                alert['type'] = 'warning'
            else:
                alert['type'] = 'caution'

            alert['date'] = str(file['time2'][i]) + ' days ago'
            alert['time'] = '12 pm'

            if difference < 0:
                alert['level'] = 'low'
            else:
                alert['level'] = 'high'

            session['heart_alerts'].append(alert)

    file2['calories_consumed'] = 1600 + (14.37 + 0.068*file2['step_counttotal'])

    for i in range(len(file2)):
        difference = file2['calories_consumed'][i] - file2['caloriesfood'][i]
        if abs(difference) > 500:
            alert = dict()
            if abs(difference) > 750:
                alert['type']  = 'warning'
            else:
                alert['type']  = 'caution'

            alert['date'] = str(file2['timediff2'][i]) + ' days ago'
            alert['time'] = '12 pm'

            if difference < 0:
                alert['level'] = 'low'
            else:
                alert['level'] = 'high'

            session['calorie_alerts'].append(alert)

    heart_rate_status = 'Normal'

    for element in session['heart_alerts']:
        if 'warning' in element.values():
            heart_rate_status = 'Warning'
            break

        elif 'caution' in element.values():
            heart_rate_status = 'Caution'

    calories_status = 'Normal'

    for element in session['calorie_alerts']:
        if 'warning' in element.values():
            calories_status = 'Warning'
            break

        elif 'caution' in element.values():
            calories_status = 'Caution'


    if heart_rate_status == 'Normal' and calories_status == 'Normal':
        overall_recommendation = 'You are doing well.'
        session['current_status'] = 'normal'

    elif heart_rate_status == 'Caution' and calories_status == 'Normal':
        overall_recommendation = 'You are fine but we recommend keeping a check on your heart rate. If you well unwell, please consult a doctor. Do not consider this as a final diagnostic.'
        session['current_status'] = 'caution'

    elif heart_rate_status == 'Normal' and calories_status == 'Caution':
        overall_recommendation = 'You are fine but we recommend keeping a check on your calorie intake.'
        session['current_status'] = 'caution'

    elif heart_rate_status == 'Caution' and calories_status == 'Caution':
        overall_recommendation = 'You are not well. Your heart rate and your calorie intake are not optimal. Please control your diet and keep an eye on your hear rate.'
        session['current_status'] = 'caution'

    elif heart_rate_status == 'Warning' and calories_status == 'Warning':
        overall_recommendation = 'Your heart rate and calorie intake is dangerously abnormal. Please consult your doctor immediately.'
        session['current_status'] = 'warning'

    elif heart_rate_status == 'Warning':
        overall_recommendation = 'Your heart rate is dangerously abnormal. Please consult your doctor immediately.'
        session['current_status'] = 'warning'

    elif calories_status == 'Warning':
        overall_recommendation = 'Your calorie intake has significantly deviated from the normal range. Please consult your dietician immediately.'
        session['current_status'] = 'warning'


    return render_template('health.html',
                            bmi = session['bmi'],
                            heart_rate_status = heart_rate_status,
                            calories_status = calories_status,
                            overall_recommendation = overall_recommendation,
                            name = session['name'],
                            current_status = session['current_status'],
                            heart_alerts = session['heart_alerts'],
                            calorie_alerts = session['calorie_alerts'])

@app.after_request
def add_header(r):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    r.headers["Pragma"] = "no-cache"
    r.headers["Expires"] = "0"
    r.headers['Cache-Control'] = 'public, max-age=0'
    return r

@app.errorhandler(404)
def page_not_found(e):
    # the flash utlity flashes a message that can be shown on the main HTML page
    flash('The URL you entered does not exist. You have been redirected to the home page')
    return redirect(url_for('login'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
