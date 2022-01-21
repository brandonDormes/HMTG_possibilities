from flask import render_template, request, session, make_response, redirect, url_for
from . import app, db
from .models import Subject, Trial
from flask_session import sessions

import pandas as pd
import random


#game_dat = pd.read_csv('Code/possibility_app/static/stim_data/HMTG_possib_stim.csv', header=0, index_col=0)
#app.app_context()
#game_dat= pd.read_csv(url_for('static', filename='stim_data/HMTG_possib_stim.csv'), header=0, index_col=0)
ntrials = 10
game_dat = pd.DataFrame({'inv':[6,10,2], 'mult':[4,2,4], 'ret':[15, 10, 2], 'IM':[24,20, 8]})

game_dat = game_dat.iloc[:ntrials]  # beta test, less trials
p1s = list(range(79))
probe_interval = 3


@app.route('/')
def index():
    return redirect('welcome') #render_template('base.html')


@app.route('/welcome')
def welcome():

    return render_template('welcome.html')


@app.route('/consent', methods=['GET', 'POST'])
def consent():
    if request.method == 'GET':
        return render_template('consent.html')
    elif request.method == 'POST':
        s_dat = request.get_json()
        session['prolific_id'] = s_dat['prolific_id']
        subj = Subject(subID=s_dat['subject_id'], prolific_id=s_dat['prolific_id'],
                       trustee_id=int(game_dat.trustee[0]), trial_order=1)
        db.session.add(subj)
        db.session.commit()
        return make_response("200")


@app.route('/instructions')
def instructions():
    print(session['prolific_id'])
    subj = Subject.query.filter_by(prolific_id=session['prolific_id']).first()
    session['subject_tableindex'] = subj.id
    session['trial'] = 0
    return render_template('instructions.html')


@app.route('/invest', methods=['GET', 'POST'])
def invest():
    random.shuffle(p1s)
    session['p1'] = p1s.pop()
    return render_template('invest.html', trial_num=session['trial']+1,
                           p1=session['p1'],
                           inv_amt=game_dat.inv[session['trial']],
                           mult=game_dat.mult[session['trial']])


@app.route('/predict', methods=['GET', 'POST'])
def predict():
    if request.method == 'GET':
        return render_template('predict.html', trial_num=session['trial']+1,
                               p1=session['p1'],
                               inv_amt=game_dat.inv[session['trial']],
                               mult=game_dat.mult[session['trial']])
    elif request.method == 'POST':
        trial_dat = request.get_json()
        tdat = Trial(trl=session['trial'],
                     p1_pic=session['p1'],
                     inv=int(game_dat.inv[session['trial']]),
                     mult=int(game_dat.mult[session['trial']]),
                     pred=int(trial_dat['trial_prediction']),
                     ret=int(game_dat.ret[session['trial']]),
                     reason='n/a',
                     subject_id=session['subject_tableindex'])
        db.session.add(tdat)
        db.session.commit()
        print(trial_dat)

        return make_response("200")


@app.route('/decision', methods=['GET', 'POST'])
def decision():
    if request.method == 'GET':
        session['trial'] = session['trial'] + 1  # FIX THIS

        return render_template('decision.html', trial_num=session['trial'], # trial was incremented after prediction
                               p1=session['p1'],
                               inv_amt=game_dat.inv[session['trial']-1],
                               mult=game_dat.mult[session['trial']-1],
                               ret=game_dat.ret[session['trial']-1],
                               interval=probe_interval,
                               last_trl=ntrials)


@app.route('/guesswhy', methods=['GET', 'POST'])
def guessWhy():
    if request.method == 'GET':
        return render_template('guesswhy.html', trial_num=session['trial'],
                               p1=session['p1'],
                               inv_amt=game_dat.inv[session['trial']-1],
                               mult=game_dat.mult[session['trial']-1],
                               ret=game_dat.ret[session['trial']-1])
    if request.method == 'POST':
        answer = request.get_json()
        print(answer)
        tdat = Trial.query.filter_by(trl=session['trial']-1, subject_id=session['subject_tableindex']).first()
        tdat.reason = answer['subject_response']
        db.session.add(tdat)
        db.session.commit()
        return make_response("200")


@app.route('/thanks')
def thanks():
    tt = random.randint(0, ntrials)
    trl = Trial.query.filter_by(trl=tt, subject_id=session['subject_tableindex']).first()
    pe = abs((trl.pred/(trl.inv*trl.mult)) - (trl.ret/(trl.inv*trl.mult)))
    acc = 1 - pe
    bonus = 2 * acc
    #bonus = ((100 - abs(((trl.pred / game_dat.IM[tt]) * 100) - ((trl.ret / game_dat.IM[tt]) * 100))) * .01) * 2
    subj = Subject.query.filter_by(prolific_id=session['prolific_id']).first()
    subj.bonus = bonus
    db.session.add(subj)
    db.session.commit()
    return render_template('thanks.html', bonus=bonus)
