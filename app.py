from flask import Flask, request, jsonify, render_template, abort, send_file
import json, os, secrets, threading, io, qrcode
from pathlib import Path
app=Flask(__name__)
DATA=json.loads((Path(__file__).parent/'data.json').read_text(encoding='utf8'))
LOCK=threading.RLock()
YEARS=['2004','2005','2006','2007','2008']
TEAMS=[{'id':i+1,'name':f'Баг {i+1}','year':y,'stats':DATA[y]['base'][:],'log':[],'token':secrets.token_urlsafe(16)} for i,y in enumerate(YEARS)]
GAME={'round':0,'phase':'lobby','submitted':{},'teams':TEAMS,'last':None,'reveal_index':0,'revision':0}
HOST_PIN=os.environ.get('HOST_PIN') or secrets.token_urlsafe(12)
def score(t):
 b,d,g,s=t['stats'];return round((b+100-d+g+s)/4)
def public():
 with LOCK:
  r=GAME['round'];phase=GAME['phase']
  return {'round':r,'phase':phase,'revision':GAME['revision'],'max_rounds':4,'submitted':[int(x) for x in GAME['submitted']], 'teams':[{'id':t['id'],'name':t['name'],'year':t['year'],'stats':t['stats'],'score':score(t),'log':t['log']} for t in TEAMS], 'events':{str(t['id']):{'title':DATA[t['year']]['events'][r][0],'desc':DATA[t['year']]['events'][r][1],'options':[{'title':c[0],'desc':c[1]} for c in DATA[t['year']]['events'][r][2]]} for t in TEAMS if r<len(DATA[t['year']]['events'])},'last':GAME['last'],'reveal_index':GAME['reveal_index']}
def authhost():
 return request.headers.get('X-Host-Pin')==HOST_PIN
def findteam():
 token=request.headers.get('X-Team-Token','')
 return next((t for t in TEAMS if secrets.compare_digest(t['token'],token)),None)
@app.get('/')
def home():return render_template('game.html')
@app.get('/api/state')
def state():return jsonify(public())
@app.post('/api/start')
def start():
 if not authhost():abort(403)
 with LOCK:
  if GAME['phase']!='lobby':return jsonify(error='Тоглоом эхэлсэн'),409
  names=(request.get_json(silent=True) or {}).get('names',[])
  for i,t in enumerate(TEAMS):
   if i<len(names):t['name']=str(names[i]).strip()[:35] or t['name']
  GAME['phase']='answer';GAME['revision']+=1
 return jsonify(public())
@app.post('/api/answer')
def answer():
 t=findteam()
 if not t:abort(403)
 d=request.get_json(silent=True) or {}
 try: choice=int(d.get('choice'))
 except: return jsonify(error='Хариулт буруу'),400
 with LOCK:
  if GAME['phase']!='answer':return jsonify(error='Хариулт авах үе биш'),409
  if str(t['id']) in GAME['submitted']:return jsonify(error='Энэ үеийн хариултыг илгээсэн'),409
  evs=DATA[t['year']]['events'];r=GAME['round']
  if r>=len(evs):return jsonify(error='Энэ багийн цохилтууд дууссан'),409
  if choice<0 or choice>=len(evs[r][2]):return jsonify(error='Сонголт буруу'),400
  GAME['submitted'][str(t['id'])]=choice;GAME['revision']+=1
 return jsonify(ok=True)
@app.post('/api/reveal')
def reveal():
 if not authhost():abort(403)
 with LOCK:
  if GAME['phase']!='answer':return jsonify(error='Үе шат тохирохгүй'),409
  active=[t for t in TEAMS if GAME['round']<len(DATA[t['year']]['events'])]
  if len(GAME['submitted'])<len(active):return jsonify(error='Бүх баг хариулаагүй байна'),409
  results=[]
  for t in active:
   r=GAME['round'];e=DATA[t['year']]['events'][r];k=GAME['submitted'][str(t['id'])];c=e[2][k];before=t['stats'][:]
   t['stats']=[max(0,min(100,x+dx)) for x,dx in zip(before,c[2])]
   entry={'title':e[0],'choice':c[0],'explanation':c[3],'delta':c[2],'before':before,'after':t['stats'][:],'round':r+1}
   t['log'].append(entry);results.append({'team':t['name'],'year':t['year'],**entry})
  GAME['last']=results;GAME['reveal_index']=0;GAME['phase']='present';GAME['revision']+=1
 return jsonify(public())
@app.post('/api/present-next')
def present_next():
 if not authhost():abort(403)
 with LOCK:
  if GAME['phase']!='present':return jsonify(error='Танилцуулах үе биш'),409
  GAME['reveal_index']+=1
  if GAME['reveal_index']>=len(GAME['last']):GAME['phase']='results'
  GAME['revision']+=1
 return jsonify(public())
@app.post('/api/next')
def next_round():
 if not authhost():abort(403)
 with LOCK:
  if GAME['phase']!='results':return jsonify(error='Эхлээд үр дүнгээ харуулна уу'),409
  GAME['round']+=1;GAME['submitted']={};GAME['last']=None
  GAME['phase']='finished' if all(GAME['round']>=len(DATA[t['year']]['events']) for t in TEAMS) else 'answer'
  GAME['revision']+=1
 return jsonify(public())
@app.post('/api/reset')
def reset():
 if not authhost():abort(403)
 with LOCK:
  GAME.update(round=0,phase='lobby',submitted={},last=None,reveal_index=0,revision=GAME['revision']+1)
  for t in TEAMS:t.update(stats=DATA[t['year']]['base'][:],log=[])
 return jsonify(public())
@app.get('/api/links')
def links():
 if not authhost():abort(403)
 return jsonify([{'id':t['id'],'name':t['name'],'year':t['year'],'token':t['token']} for t in TEAMS])
@app.get('/api/qr/<int:team_id>')
def team_qr(team_id):
 if not (authhost() or secrets.compare_digest(request.args.get('pin',''),HOST_PIN)):abort(403)
 t=next((t for t in TEAMS if t['id']==team_id),None)
 if not t:abort(404)
 url=request.host_url.rstrip('/')+'/?role=team&token='+t['token']
 img=qrcode.make(url,box_size=9,border=2)
 out=io.BytesIO();img.save(out,format='PNG');out.seek(0)
 return send_file(out,mimetype='image/png',max_age=0)
@app.get('/api/identify')
def identify():
 t=findteam()
 if not t:abort(403)
 return jsonify({'id':t['id'],'name':t['name'],'year':t['year']})
if __name__=='__main__':
 print('HOST PIN:',HOST_PIN,flush=True)
 app.run(host='0.0.0.0',port=int(os.environ.get('PORT','5000')),debug=False)
