from flask import render_template, request, session, make_response, redirect, url_for
from . import app, db
from .models import Subject, Trial
import pandas as pd
import random
import numpy as np
from sqlalchemy import or_


subs_per_p2 = 2
ntrials = 3


@app.route('/')
def index():
    # on remote set these
    # prolific_id = request.args.get('PROLIFIC_PID'),
    # flask_subId = request.args.get('flasker')

    return redirect(url_for('welcome', PROLIFIC_PID=np.random.random(),
                            SESSION_ID=np.random.random(), trial=0))


@app.route('/welcome', methods=['GET', 'POST'])
def welcome():
    return render_template('welcome.html')


@app.route('/consent', methods=['GET', 'POST'])
def consent():
    if request.method == 'GET':
        return render_template('consent.html')
    if request.method == 'POST':
        return make_response("200")

@app.route('/new_subject')
def new_subject():
    # query DB to find out what trustee/strategy subject will watch
    subjs = np.array([subj.trustee_id for subj in Subject.query.filter_by(complete=True).all()])
    # db.session.query(Subject).filter(or_(Subject.complete == True, Subject.in_progress == True)).all()])
    for p2 in [93, 97, 54, 62]:
        if len(np.where(subjs == p2)[0]) >= subs_per_p2:
            continue
        else:
            trustee_to_observe = p2
            break
    # Populated Database for New Subject
    # Probes: fixed after first trial, then uniformly sampled
    probes = [1]
    [probes.append(np.random.choice([t - 1, t, t + 1])) for t in range(1, ntrials) if t % 4 == 0]
    # Local
    game_dat = pd.read_csv('possibility_app/static/stim_data/HMTG_possib_stim.csv', header=0, index_col=0)
    # Remote
    # game_dat = pd.read_csv('/home/bryan/HMTG_possibilities/possibility_app/static/stim_data/HMTG_possib_stim.csv', header=0, index_col=0)
    game_dat = game_dat.loc[game_dat.trustee == trustee_to_observe]
    game_dat = game_dat.iloc[:ntrials]  # beta test, less trials
    game_dat = game_dat.sample(frac=1, random_state=np.random.RandomState()).reset_index(drop=True)
    game_dat['trial'] = range(1, ntrials + 1)
    # add subject
    practice = []
    practice.insert(0, {'trustee': trustee_to_observe, 'trial': 0, 'inv': 10, 'mult': 4, 'ret': 15, 'im': 40,
                        'trustee_clust': game_dat.trustee_clust.values[0]})
    game_dat = pd.concat([pd.DataFrame(practice), game_dat], ignore_index=True)
    subj = Subject(prolific_id=request.args.get('PROLIFIC_PID'),
                   in_progress=True,
                   complete=False,
                   session_id=request.args.get('SESSION_ID'),
                   trustee_id=trustee_to_observe,
                   trustee_strategy=game_dat.trustee_clust.values[0])

    db.session.add(subj)
    # add trials
    for t in range(len(game_dat)):
        db.session.add(
            Trial(trl=t,
                  p1_pic=np.random.randint(int(79)),
                  inv=int(game_dat['inv'][t]),
                  mult=int(game_dat['mult'][t]),
                  ret=int(game_dat['ret'][t]),
                  probe=t in probes,
                  prolific_id=subj.prolific_id)
        )
    db.session.commit()
    print('You have a new Subject', subj.prolific_id)
    return redirect(url_for('instructions', PROLIFIC_PID=request.args.get('PROLIFIC_PID'), SESSION_ID=request.args.get('SESSION_ID'),
                            trial=int(request.args.get('trial'))))


@app.route('/instructions', methods=['GET', 'POST'])
def instructions():
    if request.method == 'GET':

        return render_template('instructions.html')
    else:
        return make_response("200")


@app.route('/practice', methods=['GET', 'POST'])
def practice():
    if request.method == 'GET':
        tdat = Trial.query.filter_by(prolific_id=request.args.get('PROLIFIC_PID'), trl=int(request.args.get('trial'))).first()
        return render_template('invest.html', trial_num=tdat.trl,
                               p1=tdat.p1_pic,
                               inv_amt=tdat.inv,
                               mult=tdat.mult,
                               ntrials=ntrials)


@app.route('/ready')
def ready():
    return render_template('ready.html')


@app.route('/next_trial')
def next_trial():
    return redirect(url_for('invest', PROLIFIC_PID=request.args.get('PROLIFIC_PID'), SESSION_ID=request.args.get('SESSION_ID'),
                            trial=int(int(request.args.get('trial')) + 1)))


@app.route('/invest', methods=['GET', 'POST'])
def invest():
    if request.method == 'GET':
        tdat = Trial.query.filter_by(prolific_id=request.args.get('PROLIFIC_PID'), trl=int(request.args.get('trial'))).first()
        return render_template('invest.html', trial_num=tdat.trl,
                               p1=tdat.p1_pic,
                               inv_amt=tdat.inv,
                               mult=tdat.mult,
                               ntrials=ntrials)


@app.route('/predict', methods=['GET', 'POST'])
def predict():
    if request.method == 'GET':
        tdat = Trial.query.filter_by(prolific_id=request.args.get('PROLIFIC_PID'),
                                     trl=int(request.args.get('trial'))).first()
        return render_template('predict.html', trial_num=tdat.trl,
                               p1=tdat.p1_pic,
                               inv_amt=tdat.inv,
                               mult=tdat.mult,
                               ntrials=ntrials)

    elif request.method == 'POST':
        trial_dat = request.get_json()
        tdat = Trial.query.filter_by(prolific_id=trial_dat['PROLIFIC_PID'], trl=int(trial_dat['trial'])).first()
        tdat.pred = int(trial_dat['trial_prediction'])
        tdat.guess_fill = int(trial_dat['guess_fill'])
        db.session.add(tdat)
        db.session.commit()
        print(f'subject: {tdat.prolific_id},trial:{trial_dat["trial"]} , predicted: {trial_dat["trial_prediction"]}')
        return make_response("200")


@app.route('/decision', methods=['GET', 'POST'])
def decision():
    tdat = Trial.query.filter_by(prolific_id=request.args.get('PROLIFIC_PID'), trl=int(request.args.get('trial'))).first()
    if tdat.probe:
        interval = 111
    else:
        interval = 999
    return render_template('decision.html',
                           trial_num=tdat.trl,
                           p1=tdat.p1_pic,
                           inv_amt=tdat.inv,
                           mult=tdat.mult,
                           pred_amt=tdat.pred,
                           guess_fill=tdat.guess_fill,
                           ret=tdat.ret,
                           interval=interval,
                           last_trl=ntrials,
                           ntrials=ntrials)


@app.route('/guesswhy', methods=['GET', 'POST'])
def guessWhy():
    if request.method == 'GET':
        tdat = Trial.query.filter_by(prolific_id=request.args.get('PROLIFIC_PID'),
                                     trl=int(request.args.get('trial'))).first()
        return render_template('guesswhy.html',
                               trial_num=tdat.trl,
                               p1=tdat.p1_pic,
                               inv_amt=tdat.inv,
                               mult=tdat.mult,
                               ret=tdat.ret,
                               pred_amt=tdat.pred,
                               guess_fill=tdat.guess_fill,
                               ntrials=ntrials)

    elif request.method == 'POST':
        answer = request.get_json()
        tdat = Trial.query.filter_by(prolific_id=answer['PROLIFIC_PID'],
                                     trl=int(answer['trial'])).first()

        tdat.reason = answer['subject_response']
        tdat.reason_start = answer['resp_start']
        tdat.reason_rt = answer['resp_end']
        db.session.add(tdat)
        db.session.commit()
        print(f'subject: {tdat.prolific_id},trial:{answer["trial"]} , responded: {answer["subject_response"]}')
        return make_response("200")


@app.route('/thanks', methods=['GET', 'POST'])
def thanks():
    if request.method == 'GET':
        pp_id = request.args.get('PROLIFIC_PID')
        subj = Subject.query.filter_by(prolific_id=pp_id).first()
        tt = random.randint(1, ntrials-1)
        trl = Trial.query.filter_by(trl=tt, prolific_id=pp_id).first()
        pe = abs((trl.pred/(trl.inv*trl.mult)) - (trl.ret/(trl.inv*trl.mult)))
        acc = 1 - pe
        bonus = round((2 * acc), 2)
        subj.bonus = bonus
        db.session.add(subj)
        db.session.commit()
        return render_template('thanks.html', bonus=bonus)

    elif request.method == 'POST':
        answer = request.get_json()
        subj = Subject.query.filter_by(prolific_id=answer['PROLIFIC_PID']).first()

        subj.exp_feedback = answer['subject_feedback']
        subj.complete = True
        subj.in_progress = False
        db.session.add(subj)
        db.session.commit()
        print(f"Subject {subj.prolific_id} has finished!!!")
        return make_response('200')
