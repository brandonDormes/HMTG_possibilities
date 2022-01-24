from flask import render_template, request, session, make_response, redirect
from . import app, db
from .models import Subject, Trial
import pandas as pd
import random


# Local
game_dat = pd.read_csv('possibility_app/static/stim_data/HMTG_possib_stim.csv', header=0, index_col=0)
# Remote
#game_dat = pd.read_csv('/home/bryan/HMTG_project/possibility_app/static/stim_data/HMTG_possib_stim.csv', header=0, index_col=0)
#game_dat = pd.DataFrame({'inv':[6,10,2], 'mult':[4,2,4], 'ret':[15, 10, 2], 'IM':[24,20, 8]})

ntrials = 10
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


@app.route('/practice', methods=['GET', 'POST'])
def practice():
    random.shuffle(p1s)
    session['practice'] = True
    return render_template('practice.html',
                           trial_num='Practice',
                           p1=p1s[0],
                           inv_amt=10,
                           mult=4)


@app.route('/ready')
def ready():
    session['practice'] = False
    return render_template('ready.html')



@app.route('/invest', methods=['GET', 'POST'])
def invest():

    session['p1'] = p1s.pop()
    return render_template('invest.html', trial_num=session['trial']+1,
                           p1=session['p1'],
                           inv_amt=game_dat.inv[session['trial']],
                           mult=game_dat.mult[session['trial']],
                           ntrials=ntrials)


@app.route('/predict', methods=['GET', 'POST'])
def predict():
    if request.method == 'GET':
        if session['practice']:
            return render_template('predict.html', trial_num='Practice',
                                   p1=p1s[0],
                                   inv_amt=10,
                                   mult=4,
                                   ntrials='')
        else:
            return render_template('predict.html', trial_num=session['trial']+1,
                                   p1=session['p1'],
                                   inv_amt=game_dat.inv[session['trial']],
                                   mult=game_dat.mult[session['trial']],
                                   ntrials=ntrials)

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
    if session['practice']:
        return render_template('decision.html', trial_num="Practice",  # trial was incremented after prediction
                               p1=p1s[0],
                               inv_amt=10,
                               mult=4,
                               ret=15,
                               interval=probe_interval,
                               last_trl=ntrials,
                               ntrials='')
    else:
        session['trial'] = session['trial'] + 1  # FIX THIS
        if request.method == 'GET':
            return render_template('decision.html', trial_num=session['trial'], # trial was incremented after prediction
                                   p1=session['p1'],
                                   inv_amt=game_dat.inv[session['trial']-1],
                                   mult=game_dat.mult[session['trial']-1],
                                   ret=game_dat.ret[session['trial']-1],
                                   interval=probe_interval,
                                   last_trl=ntrials,
                                   ntrials=ntrials)


@app.route('/guesswhy', methods=['GET', 'POST'])
def guessWhy():
    if request.method == 'GET':
        tdat = Trial.query.filter_by(trl=session['trial'] - 1, subject_id=session['subject_tableindex']).first()
        return render_template('guesswhy.html', trial_num=session['trial'],
                               p1=session['p1'],
                               inv_amt=game_dat.inv[session['trial']-1],
                               mult=game_dat.mult[session['trial']-1],
                               ret=game_dat.ret[session['trial']-1],
                               pred=tdat.pred,
                               ntrials=ntrials)
    if request.method == 'POST':
        answer = request.get_json()
        print(answer)
        tdat = Trial.query.filter_by(trl=session['trial']-1, subject_id=session['subject_tableindex']).first()
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

    if request.method == 'POST':
        answer = request.get_json()
        subj.exp_feedback = answer['subject_feedback']
        db.session.add(subj)
        db.session.commit()
        return make_response('200')
