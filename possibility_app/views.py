from flask import render_template, request, session, make_response, redirect
from . import app, db
from .models import Subject, Trial
import pandas as pd
import random
import numpy as np
from ast import literal_eval


trustee_to_observe = 93  # 97, 54, 62
ntrials = 45
p1s = list(range(79))

@app.route('/')
def index():
    return redirect('welcome')


@app.route('/welcome')
def welcome():
    return render_template('welcome.html')


@app.route('/consent', methods=['GET', 'POST'])
def consent():
    if request.method == 'GET':
        return render_template('consent.html')
    elif request.method == 'POST':

        return make_response("200")


@app.route('/getID', methods=['GET', 'POST'])
def getID():
    if request.method == 'GET':
        return render_template('getID.html')
    elif request.method == 'POST':
        s_dat = request.get_json()
        session['prolific_id'] = s_dat['prolific_ID']
        subj = Subject(subID=777, prolific_id=s_dat['prolific_ID'],
                       trustee_id=int(trustee_to_observe), trial_order=1)
        db.session.add(subj)
        db.session.commit()
        print('You have a new Subject', s_dat)
        return redirect('instructions')


@app.route('/instructions', methods=['GET', 'POST'])
def instructions():
    if request.method == 'GET':
        subj = Subject.query.filter_by(prolific_id=session['prolific_id']).last()
        session['subject_tableindex'] = subj.id
        session['trial'] = 0
        return render_template('instructions.html')
    else:
        return make_response("200")



@app.route('/practice', methods=['GET', 'POST'])
def practice():
    random.shuffle(p1s)
    session['p1'] = p1s[np.random.randint(int(len(p1s)))]
    session['practice'] = True
    return render_template('practice.html',
                           trial_num='Practice',
                           p1=session['p1'],
                           inv_amt=10,
                           mult=4)


@app.route('/ready')
def ready():
    # Probes: fixed after first trial, then uniformly sampled
    probes = [0]
    [probes.append(np.random.choice([t - 1, t, t + 1])) for t in range(1, ntrials) if t % 4 == 0]
    session['probes'] = str(probes)
    # Local
    game_dat = pd.read_csv('possibility_app/static/stim_data/HMTG_possib_stim.csv', header=0, index_col=0)
    # Remote
    # game_dat = pd.read_csv('/home/bryan/HMTG_project/possibility_app/static/stim_data/HMTG_possib_stim.csv', header=0, index_col=0)
    game_dat = game_dat.loc[game_dat.trustee == trustee_to_observe]
    game_dat = game_dat.iloc[:ntrials]  # beta test, less trials
    game_dat = game_dat.sample(frac=1, random_state=np.random.RandomState()).reset_index(drop=True)
    game_dat['trial'] = range(ntrials)
    session['stim'] = game_dat.to_dict()
    session['practice'] = False
    return render_template('ready.html')


@app.route('/invest', methods=['GET', 'POST'])
def invest():
    session['p1'] = p1s[np.random.randint(int(len(p1s)))]
    return render_template('invest.html', trial_num=session['trial']+1,
                           p1=session['p1'],
                           inv_amt=session['stim']['inv'][str(session['trial'])],
                           mult=session['stim']['mult'][str(session['trial'])],
                           ntrials=ntrials)


@app.route('/predict', methods=['GET', 'POST'])
def predict():
    if request.method == 'GET':
        if session['practice']:
            return render_template('predict.html', trial_num='Practice',
                                   p1=session['p1'],
                                   inv_amt=10,
                                   mult=4,
                                   ntrials='')
        else:
            return render_template('predict.html', trial_num=session['trial']+1,
                                   p1=session['p1'],
                                   inv_amt=session['stim']['inv'][str(session['trial'])],
                                   mult=session['stim']['mult'][str(session['trial'])],
                                   ntrials=ntrials)

    elif request.method == 'POST':
        if not session['practice']:
            trial_dat = request.get_json()
            tdat = Trial(trl=session['trial'],
                         p1_pic=session['p1'],
                         inv=int(session['stim']['inv'][str(session['trial'])]),
                         mult=int(session['stim']['mult'][str(session['trial'])]),
                         pred=int(trial_dat['trial_prediction']),
                         ret=int(session['stim']['ret'][str(session['trial'])]),
                         reason='n/a',
                         subject_id=session['subject_tableindex'])
            db.session.add(tdat)
            db.session.commit()
            print(trial_dat)

        return make_response("200")


@app.route('/decision', methods=['GET', 'POST'])
def decision():
    if session['practice']:
        return render_template('decision.html', trial_num="Practice",  # trial was incremented after prediction
                               p1=session['p1'],
                               inv_amt=10,
                               mult=4,
                               ret=15,
                               interval=999,
                               last_trl=ntrials,
                               ntrials='')
    else:
        session['trial'] = session['trial'] + 1  # FIX THIS
        if request.method == 'GET':
            if session['trial']-1 in literal_eval(session['probes']):
                interval = 111
            else:
                interval = 999
            return render_template('decision.html', trial_num=session['trial'],  # trial was incremented after prediction
                                   p1=session['p1'],
                                   inv_amt=session['stim']['inv'][str(session['trial']-1)],
                                   mult=session['stim']['mult'][str(session['trial']-1)],
                                   ret=session['stim']['ret'][str(session['trial']-1)],
                                   interval=interval,
                                   last_trl=ntrials,
                                   ntrials=ntrials)


@app.route('/guesswhy', methods=['GET', 'POST'])
def guessWhy():
    if request.method == 'GET':
        tdat = Trial.query.filter_by(trl=session['trial'] - 1, subject_id=session['subject_tableindex']).first()
        return render_template('guesswhy.html', trial_num=session['trial'],
                               p1=session['p1'],
                               inv_amt=session['stim']['inv'][str(session['trial'] - 1)],
                               mult=session['stim']['mult'][str(session['trial'] - 1)],
                               ret=session['stim']['ret'][str(session['trial'] - 1)],
                               pred=tdat.pred,
                               ntrials=ntrials)

    elif request.method == 'POST':
        tdat = Trial.query.filter_by(trl=session['trial'] - 1, subject_id=session['subject_tableindex']).first()
        answer = request.get_json()
        print(answer)
        tdat.reason = answer['subject_response']
        tdat.reason_start = answer['resp_start']
        tdat.reason_rt = answer['resp_end']
        db.session.add(tdat)
        db.session.commit()
        return make_response("200")


@app.route('/thanks', methods=['GET', 'POST'])
def thanks():
    subj = Subject.query.filter_by(prolific_id=session['prolific_id']).first()
    if request.method == 'GET':
        tt = random.randint(1, ntrials-1)
        trl = Trial.query.filter_by(trl=tt, subject_id=session['subject_tableindex']).first()
        pe = abs((trl.pred/(trl.inv*trl.mult)) - (trl.ret/(trl.inv*trl.mult)))
        acc = 1 - pe
        bonus = round((2 * acc), 2)
        #bonus = ((100 - abs(((trl.pred / game_dat.IM[tt]) * 100) - ((trl.ret / game_dat.IM[tt]) * 100))) * .01) * 2
        subj.bonus = bonus
        db.session.add(subj)
        db.session.commit()
        return render_template('thanks.html', bonus=bonus)

    elif request.method == 'POST':
        answer = request.get_json()
        subj.exp_feedback = answer['subject_feedback']
        db.session.add(subj)
        db.session.commit()
        return make_response('200')
