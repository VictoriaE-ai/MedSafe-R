"""Reproduce all MedSafe-R charts, tables and baseline model evaluations.
Run: python analysis.py [path/to/workbook.xlsx]
Outputs are written beside this script. All input data are synthetic.
"""
from pathlib import Path
import sys,json,base64,html,hashlib,platform,warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter
from matplotlib.backends.backend_pdf import PdfPages
from scipy.stats import spearmanr
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder,StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import roc_auc_score,average_precision_score,roc_curve,precision_recall_curve,brier_score_loss
from sklearn.calibration import calibration_curve
import sklearn,scipy
ROOT=Path(__file__).resolve().parent
SOURCE=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'data/MedSafe_R_Dataset_v1.3_cleaned.xlsx'
for folder in ['charts','tables']: (ROOT/folder).mkdir(exist_ok=True)
SNAP=pd.Timestamp('2026-07-31');START=pd.Timestamp('2024-01-01');SEED=20261020
w=pd.read_excel(SOURCE,sheet_name=None)
i=w['Device_Inventory'].copy();m=w['Maintenance_Events'].copy();s=w['Safety_Events'].copy();o=w['Monthly_Operations'].copy();f=w['ML_Feature_Table'].copy()
r=m[m.event_type.eq('Corrective Repair')].sort_values(['device_id','event_date','maintenance_event_id']).copy()
BLUE='#2367a7';TEAL='#087e83';ORANGE='#c97029';RED='#ac4050';GRAY='#84919a';INK='#18324b'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'axes.labelcolor':INK,'text.color':INK,'axes.titleweight':'bold','axes.titlesize':12,'axes.grid':False,'savefig.facecolor':'white','figure.facecolor':'white'})
pages=[];tables={};findings=[]
def table(name,df):
 tables[name]=df.copy();df.to_csv(ROOT/'tables'/f'{name}.csv',index=False)
def page(title,subtitle):
 fig,ax=plt.subplots(2,2,figsize=(16,11));fig.suptitle(title,x=.06,y=.965,ha='left',fontsize=22,fontweight='bold',color=INK)
 fig.text(.06,.922,subtitle,ha='left',fontsize=10.5,color='#506274');fig.subplots_adjust(left=.17,right=.97,bottom=.10,top=.84,hspace=.50,wspace=.58)
 return fig,ax.flatten()
def finish(fig,name,foot):
 fig.text(.06,.032,foot,fontsize=9,color='#506274',va='bottom');fig.savefig(ROOT/'charts'/f'{name}.png',dpi=160);pages.append((name,fig))
def bars(ax,labels,values,title,xlabel,percent=False,color=BLUE,dec=1):
 labels=list(labels);values=np.array(values);y=np.arange(len(labels));ax.barh(y,values,color=color,height=.65);ax.set_yticks(y,labels);ax.invert_yaxis();ax.set_title(title,loc='left',pad=12);ax.set_xlabel(xlabel);ax.set_xlim(0,max(values.max()*1.25,1));ax.xaxis.grid(True,alpha=.17);ax.set_axisbelow(True)
 for yy,v in zip(y,values):ax.text(v+max(values.max(),1)*.018,yy,f'{v:.{dec}f}'+('%' if percent else ''),va='center',fontsize=9)
def wilson(k,n):
 k=np.asarray(k,dtype=float);n=np.asarray(n,dtype=float);z=1.96;p=k/n;den=1+z*z/n;c=(p+z*z/(2*n))/den;half=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/den;return c-half,c+half
# Common audits and exact windows.
assert len(i)==1200 and i.device_id.is_unique
for df,key in [(m,'maintenance_event_id'),(s,'safety_event_id')]:
 assert df[key].is_unique and df.device_id.isin(i.device_id).all()
 assert (df.event_date<=SNAP).all()
 assert (df.event_date>=df.device_id.map(i.set_index('device_id').commissioning_date)).all()
for days,col,df in [(90,'corrective_repairs_90d',r),(365,'corrective_repairs_365d',r),(365,'safety_events_365d',s)]:
 z=df[df.event_date.between(SNAP-pd.Timedelta(days=days-1),SNAP)].groupby('device_id').size()
 assert np.array_equal(f[col],f.device_id.map(z).fillna(0))
valid_o=o[~o.hours_check.str.startswith('Fail')].copy();assert len(o)-len(valid_o)==9
# 1. Overdue preventive maintenance.
i['overdue']=i.pm_overdue_days.gt(0);over=int(i.overdue.sum());assert over==253
pmtype=i.groupby('device_type').agg(devices=('device_id','size'),overdue=('overdue','sum')).reset_index();pmtype['overdue_pct']=100*pmtype.overdue/pmtype.devices
pmdept=i.groupby('department').agg(devices=('device_id','size'),overdue=('overdue','sum')).reset_index();pmdept['overdue_pct']=100*pmdept.overdue/pmdept.devices
for name,d in [('overdue_by_type',pmtype),('overdue_by_department',pmdept)]:table(name,d)
bands=pd.cut(i.loc[i.overdue,'pm_overdue_days'],[0,30,60,90,180,np.inf],labels=['1-30','31-60','61-90','91-180','181+']).value_counts(sort=False)
source=i.groupby('pm_date_source').agg(devices=('device_id','size'),overdue=('overdue','sum')).reset_index();table('pm_source_assumptions',source)
latest=m[m.event_type.eq('Preventive Maintenance')].groupby('device_id').event_date.max();j=i.copy();j['log_pm']=j.device_id.map(latest);j['log_due']=j.log_pm+pd.to_timedelta(j.maintenance_interval_days,unit='D');log_known=j.log_pm.notna();log_over=int((j.log_due<SNAP).sum())
table('overdue_lateness_bands', bands.rename_axis('days_overdue_band').reset_index(name='devices'))
table('pm_source_sensitivity',pd.DataFrame({'scenario':['Inventory precedence','Logged PM only'],'devices_with_known_dates':[1200,int(log_known.sum())],'overdue':[over,log_over],'unknown_dates':[0,int((~log_known).sum())]}))
top=i[i.overdue].sort_values(['clinical_criticality','pm_overdue_days'],ascending=[True,False]);table('overdue_device_register',top[['device_id','device_type','department','clinical_criticality','pm_overdue_days','last_pm_date','next_pm_due','pm_date_source','pm_date_assumed']])
fig,ax=page('01 | Overdue preventive maintenance',f'{over:,} / {len(i):,} devices overdue ({over/len(i):.1%}) at 31 July 2026. Inventory-based estimate; PM source assumptions apply.')
d=pmtype.sort_values('overdue',ascending=False);bars(ax[0],d.device_type,d.overdue,'Overdue workload by device type','Devices overdue',dec=0)
d=pmdept.sort_values('overdue_pct',ascending=False);bars(ax[1],d.department,d.overdue_pct,'Overdue share by department','Percent of department devices',True)
ax[2].bar(bands.index.astype(str),bands.values,color=TEAL);ax[2].set_title('How late are the overdue devices?',loc='left');ax[2].set_xlabel('Days overdue');ax[2].set_ylabel('Devices');ax[2].bar_label(ax[2].containers[0],padding=3)
ax[3].bar(['Inventory precedence\n(all 1,200 devices)','Log-supported only\n(1,161 devices)'],[over,log_over],color=[BLUE,ORANGE]);ax[3].bar_label(ax[3].containers[0],padding=3);ax[3].set_title('PM-source sensitivity: counts, not intervention',loc='left');ax[3].set_ylabel('Devices overdue');ax[3].text(.02,.92,'39 devices have no logged PM.\nDifferent evidence coverage; not like-for-like rates.',transform=ax[3].transAxes,va='top',fontsize=9)
finish(fig,'01_overdue_pm','Synthetic data. PM precedence: later of inventory and valid PM log. 639 inventory-only dates; 11 commissioning placeholders.\nFull overdue-device register and source breakdown are supplied as CSV tables.')
findings.append(f'Overdue PM: {over} devices ({over/len(i):.1%}); log-only evidence gives {log_over} overdue among {int(log_known.sum())} devices with a recorded PM, with 39 unknown.')
# 2. Downtime and repeat repairs.
monthly=m.assign(month=m.event_date.dt.to_period('M')).pivot_table(index='month',columns='event_type',values='downtime_hours',aggfunc='sum',fill_value=0).reindex(pd.period_range(START,SNAP,freq='M'),fill_value=0);monthly.index.name='month';table('monthly_downtime',monthly.reset_index())
dt=m.groupby('event_type').agg(events=('device_id','size'),hours=('downtime_hours','sum')).reset_index();table('downtime_by_event_type',dt)
repairs=i.device_id.map(r.groupby('device_id').size()).fillna(0).astype(int);hist=repairs.clip(upper=4).value_counts().reindex(range(5),fill_value=0)
table('corrective_repairs_per_device_distribution',hist.rename_axis('repair_count_capped_at_4').reset_index(name='devices'))
r['gap_days']=r.groupby('device_id').event_date.diff().dt.days;r['repeat_within90']=r.gap_days.le(90);repeat_n=int(r.repeat_within90.sum())
cat=r.groupby('failure_category').agg(repairs=('device_id','size'),downtime_hours=('downtime_hours','sum')).reset_index().sort_values('downtime_hours',ascending=False);table('failure_categories',cat)
chronic=r.groupby('device_id').agg(repairs=('device_id','size'),repair_downtime_hours=('downtime_hours','sum'),repeat_jobs_within90=('repeat_within90','sum')).reset_index().merge(i[['device_id','device_type','department']],on='device_id');table('device_repair_history',chronic)
fig,ax=page('02 | Downtime and recurring repairs',f'{len(r):,} corrective repairs; {repeat_n} occurred within 90 days of the previous corrective repair on the same device.')
for c,color in zip(monthly.columns,[TEAL,BLUE,ORANGE]):ax[0].plot(monthly.index.to_timestamp(),monthly[c],label=c,color=color,lw=1.8)
ax[0].set_title('Maintenance-associated downtime by month',loc='left');ax[0].set_ylabel('Sum of recorded downtime hours');ax[0].legend(fontsize=8,loc='upper left');ax[0].tick_params(axis='x',rotation=30)
labels=['Corrective Repair','Preventive Maintenance','Calibration'];d=dt.set_index('event_type').reindex(labels);vals=np.array([d.events/d.events.sum(),d.hours/d.hours.sum()])*100;left=np.zeros(2)
for n,color,values in zip(labels,[BLUE,TEAL,ORANGE],vals.T):ax[1].barh(['Event count','Downtime hours'],values,left=left,label=n,color=color);left+=values
ax[1].set_xlim(0,100);ax[1].set_xlabel('Share (%)');ax[1].set_title('Repair workload versus downtime burden',loc='left');ax[1].legend(fontsize=8,loc='lower center',bbox_to_anchor=(.5,-.40),ncol=1)
ax[2].bar(['0','1','2','3','4+'],hist.values,color=BLUE);ax[2].bar_label(ax[2].containers[0],padding=3);ax[2].set_title('Recorded corrective repairs per device',loc='left');ax[2].set_xlabel('Repairs, Jan 2024-Jul 2026');ax[2].set_ylabel('Devices')
bars(ax[3],cat.failure_category,cat.downtime_hours,'Downtime burden by failure category','Recorded corrective downtime hours',dec=0)
finish(fig,'02_downtime_recurrence','Repeat = another corrective repair within 90 calendar days, regardless of category; not proof of the same unresolved fault.\nRecorded downtime sums are event burden, not validated fleet unavailability: event durations may overlap.')
share=100*r.downtime_hours.sum()/m.downtime_hours.sum();findings.append(f'Corrective repairs account for {share:.1f}% of recorded maintenance downtime. {int((repairs>=3).sum())} devices have at least 3 recorded repairs.')
# 3. Comparisons with time-at-risk denominator.
i['observed_years']=((SNAP-i.commissioning_date.clip(lower=START)).dt.days+1)/365.25
i['repairs']=repairs;i['repair_downtime']=i.device_id.map(r.groupby('device_id').downtime_hours.sum()).fillna(0)
def comparison(group):
 d=i.groupby(group).agg(devices=('device_id','size'),device_years=('observed_years','sum'),repairs=('repairs','sum'),repair_downtime=('repair_downtime','sum'),overdue=('overdue','sum')).reset_index();d['repairs_per_100_device_years']=100*d.repairs/d.device_years;d['downtime_per_device_year']=d.repair_downtime/d.device_years;d['overdue_pct']=100*d.overdue/d.devices;return d
ct=comparison('device_type');cd=comparison('department');table('maintenance_comparison_types',ct);table('maintenance_comparison_departments',cd)
fig,ax=page('03 | Maintenance needs: compare burden and rates','Repair rates use calendar device-years since commissioning or 1 Jan 2024, whichever is later; they are not operating-hour failure rates.')
d=ct.sort_values('repairs_per_100_device_years',ascending=False);bars(ax[0],d.device_type,d.repairs_per_100_device_years,'Corrective repairs by device type','Repairs per 100 observed device-years')
d=cd.sort_values('repairs_per_100_device_years',ascending=False);bars(ax[1],d.department,d.repairs_per_100_device_years,'Corrective repairs by department','Repairs per 100 observed device-years')
d=ct.sort_values('overdue_pct',ascending=False);bars(ax[2],d.device_type,d.overdue_pct,'Overdue PM share by device type','Percent of devices',True,color=TEAL)
d=cd.sort_values('downtime_per_device_year',ascending=False);bars(ax[3],d.department,d.downtime_per_device_year,'Repair downtime burden by department','Recorded hours per observed device-year',color=TEAL)
finish(fig,'03_maintenance_comparisons','Descriptive comparisons. No claim of causal or statistically established differences; age, type mix, utilisation and logging differ.\nTime-at-risk assumes continuous observation after commissioning within the study; decommissioning dates are unavailable.')
# 4. Historical safety associations: device denominators, same-period events.
recent_s=s[s.event_date.between(pd.Timestamp('2025-08-01'),SNAP)]
f['safety_any_365']=f.device_id.isin(recent_s.device_id).astype(int)
buckets=pd.cut(f.corrective_repairs_365d,[-1,0,1,2,np.inf],labels=['0','1','2','3+']);assoc=f.groupby(buckets,observed=False).agg(n=('device_id','size'),affected=('safety_any_365','sum')).reset_index(names='repairs');assoc['pct']=100*assoc.affected/assoc.n;lo,hi=wilson(assoc.affected,assoc.n);assoc['lo_pct']=100*lo;assoc['hi_pct']=100*hi;table('safety_by_repair_history',assoc)
st=i.groupby('device_type').agg(devices=('device_id','size')).reset_index();st['affected_devices']=st.device_type.map(s.merge(i[['device_id','device_type']],on='device_id').groupby('device_type').device_id.nunique()).fillna(0).astype(int);st['pct']=100*st.affected_devices/st.devices;table('safety_affected_devices_by_type',st);assert st.affected_devices.sum()==s.device_id.nunique()
features=['corrective_repairs_365d','avg_repair_hours','pm_overdue_days','device_age_years','calibration_drift_latest_pct','alarm_count_30d'];corr=pd.DataFrame([{'indicator':c,'rho':float(spearmanr(f[c],f.safety_any_365).statistic)} for c in features]);table('safety_rank_correlations',corr)
harm=pd.crosstab(s.potential_harm_level,s.actual_harm_level).reindex(index=['Low','Moderate','High','Critical'],columns=['No harm','Low','Moderate','Severe'],fill_value=0);table('potential_actual_harm',harm.reset_index())
fig,ax=page('04 | Reliability indicators and simulated safety events',f'{len(s)} recorded events affect {s.device_id.nunique()} distinct devices. Associations below do not establish causality or future prediction.')
ax[0].bar(assoc.repairs.astype(str),assoc.pct,color=BLUE);ax[0].errorbar(np.arange(len(assoc)),assoc.pct,yerr=[assoc.pct-assoc.lo_pct,assoc.hi_pct-assoc.pct],fmt='none',color=INK,capsize=4);ax[0].set_title('Past-year safety events by repair history',loc='left');ax[0].set_xlabel('Corrective repairs in the same 365-day window');ax[0].set_ylabel('Devices with at least one event (%)');ax[0].set_ylim(0,max(assoc.hi_pct)+6)
for x,row in enumerate(assoc.itertuples()):ax[0].text(x,row.hi_pct+1,f'{row.affected}/{row.n}',ha='center',fontsize=8)
d=st.sort_values('pct',ascending=False);bars(ax[1],d.device_type,d.pct,'Affected devices by type: full recorded period','Percent of devices with 1+ safety events',True)
cs=corr.sort_values('rho');names={'corrective_repairs_365d':'Repairs, 365 days','avg_repair_hours':'Mean repair labour','pm_overdue_days':'Days PM overdue','device_age_years':'Device age','calibration_drift_latest_pct':'Latest calibration drift','alarm_count_30d':'July alarm count'};ax[2].barh([names[x] for x in cs.indicator],cs.rho,color=TEAL);ax[2].axvline(0,color=GRAY,lw=1);ax[2].set_xlim(min(-.05,cs.rho.min()-.03),max(.25,cs.rho.max()+.03));ax[2].set_title('Rank association with past-year event presence',loc='left');ax[2].set_xlabel('Spearman correlation (rho)')
im=ax[3].imshow(harm.values,cmap='Blues',aspect='auto');ax[3].set_xticks(range(4),harm.columns);ax[3].set_yticks(range(4),harm.index);ax[3].set_xlabel('Actual harm');ax[3].set_ylabel('Potential harm');ax[3].set_title('Potential harm versus recorded actual harm',loc='left')
for rr in range(4):
 for cc in range(4):ax[3].text(cc,rr,str(harm.iloc[rr,cc]),ha='center',va='center',color='white' if harm.iloc[rr,cc]>harm.values.max()*.6 else INK)
finish(fig,'04_safety_associations','Error bars: Wilson 95% intervals, descriptive of the synthetic sample only. Small groups are unstable.\nPast-year window: 1 Aug 2025-31 Jul 2026. Same-window associations may include repairs following safety events; no temporal causal ordering.')
# 5. Predictive baselines: no fitting outside each training fold.
num=['device_age_years','utilisation_90d_pct','pm_overdue_days','corrective_repairs_90d','corrective_repairs_365d','repeat_failures_90d','downtime_90d_hours','avg_repair_hours','no_fault_found_365d','safety_events_365d','high_potential_harm_events_365d','alarm_count_30d','error_code_count_30d','calibration_drift_latest_pct','network_disconnects_30d','replacement_cost_gbp','corrective_repairs_total','mtbf_measured_days','days_since_last_repair']
catcols=['device_type','clinical_criticality','site','support_status'];X=f[num+catcols].copy()
# Harmonise age to the inventory calculation; all other inputs use documented cleaned features.
X['device_age_years']=f.device_id.map(i.set_index('device_id').device_age_years)
assert not any(x in X.columns for x in ['mtbf_days','data_quality_score','engineering_priority_score','priority_band','failure_next_30d','safety_event_next_90d','device_id'])
def pipeline(model):
 prep=ColumnTransformer([('num',Pipeline([('impute',SimpleImputer(strategy='median',add_indicator=True)),('scale',StandardScaler())]),num),('cat',Pipeline([('impute',SimpleImputer(strategy='most_frequent')),('encode',OneHotEncoder(handle_unknown='ignore',sparse_output=False))]),catcols)])
 return Pipeline([('prepare',prep),('model',model)])
metrics=[];model_notes=[]
for target,title,slug in [('failure_next_30d','Failure in the next 30 days','05_failure_models'),('safety_event_next_90d','Safety event in the next 90 days','05b_safety_models')]:
 y=f[target].to_numpy().astype(int);n=len(y);pos=int(y.sum());prev=y.mean();preds={};fold_rows=[];repeat_scores={}
 for name in ['Logistic regression','Random forest','Prevalence baseline']:
  pp=np.zeros((3,n))
  for repeat in range(3):
   cv=StratifiedKFold(n_splits=5,shuffle=True,random_state=SEED+repeat)
   for fold,(tr,te) in enumerate(cv.split(X,y)):
    if name=='Prevalence baseline':p=np.full(len(te),y[tr].mean())
    else:
     model=LogisticRegression(max_iter=1500,C=1.0,random_state=SEED) if name=='Logistic regression' else RandomForestClassifier(n_estimators=160,min_samples_leaf=8,max_features='sqrt',random_state=SEED+repeat,n_jobs=1)
     pipe=pipeline(model);pipe.fit(X.iloc[tr],y[tr]);p=pipe.predict_proba(X.iloc[te])[:,1]
    pp[repeat,te]=p
    fold_rows.extend([{'target':target,'model':name,'repeat':repeat+1,'fold':fold+1,'device_id':f.device_id.iloc[k],'label':int(y[k]),'score':float(v)} for k,v in zip(te,p)])
  assert np.isfinite(pp).all() and ((pp>=0)&(pp<=1)).all()
  preds[name]=pp.mean(axis=0);repeat_scores[name]=[roc_auc_score(y,z) for z in pp]
 preds['Engineering heuristic']=f.engineering_priority_score.to_numpy(dtype=float)/100
 out=f[['device_id',target]].copy()
 for name,p in preds.items():out[name]=p
 table(f'{target}_oof_predictions',out);table(f'{target}_fold_predictions',pd.DataFrame(fold_rows))
 rng=np.random.default_rng(SEED);positive=np.flatnonzero(y==1);negative=np.flatnonzero(y==0);boot_indices=[np.r_[rng.choice(positive,len(positive),replace=True),rng.choice(negative,len(negative),replace=True)] for _ in range(1000)]
 result=[]
 for name,p in preds.items():
  auc=roc_auc_score(y,p);ap=average_precision_score(y,p);boots=np.array([roc_auc_score(y[idx],p[idx]) for idx in boot_indices]);lo,hi=np.quantile(boots,[.025,.975]);top=np.argsort(-p,kind='stable')[:120];tp=int(y[top].sum());capture=tp/pos
  row={'target':target,'model':name,'positives':pos,'n':n,'prevalence':prev,'roc_auc':auc,'auc_ci_low':lo,'auc_ci_high':hi,'average_precision':ap,'top120_positives':tp if name!='Prevalence baseline' else np.nan,'top120_precision':tp/120 if name!='Prevalence baseline' else np.nan,'top120_recall':capture if name!='Prevalence baseline' else np.nan,'brier_score':brier_score_loss(y,p) if name!='Engineering heuristic' else np.nan,'repeat_auc_min':min(repeat_scores[name]) if name in repeat_scores else np.nan,'repeat_auc_max':max(repeat_scores[name]) if name in repeat_scores else np.nan};result.append(row);metrics.append(row)
 table(f'{target}_metrics',pd.DataFrame(result))
 fig,ax=page('05 | '+title+' - synthetic-label baseline',f'{pos} positive labels / {n:,} devices ({prev:.2%}). Fixed model settings; stratified 5-fold CV repeated 3 times; averaged out-of-fold scores.')
 colors={'Logistic regression':BLUE,'Random forest':TEAL,'Engineering heuristic':ORANGE,'Prevalence baseline':GRAY}
 for name,p in preds.items():
  if name=='Prevalence baseline':continue
  a,b,_=roc_curve(y,p);row=next(q for q in result if q['model']==name);ax[0].plot(a,b,label=f'{name} ({row["roc_auc"]:.2f})',color=colors[name]);rec,prec=None,None;pr,re,_=precision_recall_curve(y,p);ax[1].step(re,pr,where='post',label=name,color=colors[name],lw=1.5)
 ax[0].plot([0,1],[0,1],'--',color=GRAY,lw=1);ax[0].set(xlabel='False-positive rate',ylabel='True-positive rate',title='ROC ranking performance',xlim=(0,1),ylim=(0,1));ax[0].legend(fontsize=8,loc='lower right')
 ax[1].axhline(prev,ls='--',color=GRAY,label=f'Event prevalence ({prev:.1%})');ax[1].set(xlabel='Recall',ylabel='Precision',title='Precision-recall performance',xlim=(0,1),ylim=(0,1));ax[1].legend(fontsize=8,loc='upper right')
 rr=[q for q in result if q['model']!='Prevalence baseline'];yy=np.arange(len(rr));vv=np.array([q['roc_auc'] for q in rr]);ll=np.array([q['auc_ci_low'] for q in rr]);hh=np.array([q['auc_ci_high'] for q in rr]);ax[2].errorbar(vv,yy,xerr=[vv-ll,hh-vv],fmt='o',color=BLUE,capsize=4);ax[2].set_yticks(yy,[q['model'] for q in rr]);ax[2].axvline(.5,color=GRAY,ls='--');ax[2].set(xlabel='ROC AUC; conditional bootstrap 95% interval',title='Uncertainty in ranking performance',xlim=(min(.35,ll.min()-.03),max(.85,hh.max()+.03)))
 ax[3].barh([q['model'] for q in rr],[q['top120_positives'] for q in rr],color=[colors[q['model']] for q in rr]);ax[3].set_xlim(0,max(q['top120_positives'] for q in rr)+5);ax[3].set_title('What a 120-device review budget finds',loc='left');ax[3].set_xlabel('Positive labels among the 120 highest scores')
 for idx,q in enumerate(rr):ax[3].text(q['top120_positives']+.3,idx,f'{int(q["top120_positives"])}/{pos} ({q["top120_recall"]:.0%} recall)',va='center',fontsize=9)
 finish(fig,slug,'Intervals resample devices with fixed out-of-fold scores; they do not include retraining or generator uncertainty. No independent external test.\nSynthetic labels lack future event verification. Heuristic is a ranking score, not a probability; shared generator assumptions may favour it.')
 model_notes.append(f'{title}: logistic AUC {result[0]["roc_auc"]:.3f}; random forest {result[1]["roc_auc"]:.3f}; heuristic {result[3]["roc_auc"]:.3f}.')
 print('MODELS',target,model_notes[-1],flush=True)
# Metadata, reproducibility and a PDF reading guide.
table('all_model_metrics',pd.DataFrame(metrics))
meta={'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'seed':SEED,'python':platform.python_version(),'pandas':pd.__version__,'numpy':np.__version__,'sklearn':sklearn.__version__,'scipy':scipy.__version__,'features':num+catcols,'numeric_missing_strategy':'Training-fold median + missing indicators; scaling fitted within fold','categorical_strategy':'Training-fold most frequent + one-hot; unknown ignored','model_settings':{'logistic':'C=1, max_iter=1500, no class weighting','forest':'160 trees, min_samples_leaf=8, max_features=sqrt, no class weighting'},'cv':'5 stratified folds x 3 repeats, no tuning; per-device mean OOF prediction','ci':'1000 stratified device bootstraps conditional on fixed mean OOF scores','top120':'Stable descending score order; tied scores use workbook row order. No top120 metric for non-ranking baseline.'}
(ROOT/'methods.json').write_text(json.dumps(meta,indent=2));(ROOT/'requirements.txt').write_text('\n'.join([f'pandas=={pd.__version__}',f'numpy=={np.__version__}',f'scikit-learn=={sklearn.__version__}',f'scipy=={scipy.__version__}',f'matplotlib=={matplotlib.__version__}','openpyxl'])+'\n')
methods=[
'All records, manufacturers, regulatory signals and outcomes are synthetic. Results show analytical methods, not validated device risk or patient-safety benefits.',
'Snapshot: 31 July 2026. Historical event windows are exactly 90 days (3 May-31 July 2026) and 365 days (1 August 2025-31 July 2026), inclusive. July telemetry is a calendar month; utilisation is the May-July mean.',
'Overdue PM uses the later of inventory and valid logged PM. Source coverage: 550 log-supported, 639 inventory-only, 11 commissioning placeholders. The latter do not prove PM occurred. Sensitivity counts use a different evidence denominator.',
'Nine monthly records fail hours plausibility checks. They are excluded from hours/utilisation analysis; none is in May-July. Reported downtime uses maintenance logs, not monthly operations; missing commissioning-month exposure remains an assumption.',
'Corrective repairs are not guaranteed independent failures. Repeat jobs within 90 days may be unrelated categories. Mean repair intervals are calendar gaps, not operating-hour MTBF; legacy 999 values are excluded from modelling.',
'Safety affected-device counts use distinct device IDs. Historical associations use binary presence of an event in the same 365-day period and do not establish event ordering or causality. Wilson intervals are descriptive only.',
'Learning pipelines fit preprocessing only on training folds. Models have fixed settings, no hyperparameter search. No legacy MTBF, ID, priority score/band, synthetic quality score or target enters the trained predictors. Missing repair intervals are imputed within folds with indicators.',
'Cross-validation assesses synthetic-label discrimination among held-out devices in the same dataset. It is not prospective, temporal or external validation. Some predictors and labels may share generator logic, and labels have not been checked against future event records.',
'Conditional bootstrap AUC intervals quantify resampling uncertainty for fixed OOF scores. They do not capture model refitting, correlated site effects or uncertainty in the data generator. Comparisons are descriptive, not significance tests.',
'Class weighting and resampling are not used; rare-event performance is reported with average precision, Brier score (trained probability models only), and positives found in a fixed top-120 review budget. No deployment threshold is validated. Calibration requires further study.',
'CSV tables, fold assignments/predictions, exact environment versions and source hash are included. Run python analysis.py after installing requirements.txt. Each HTML chart has a corresponding table view; chart images themselves are static.'
]
import textwrap
cover=plt.figure(figsize=(16,11));cover.text(.07,.91,'VICTORYHEALTH ANALYTICS',fontsize=13,color=TEAL,fontweight='bold');cover.text(.07,.83,'MedSafe-R',fontsize=40,fontweight='bold');cover.text(.07,.76,'Reliability, maintenance and patient-safety analysis',fontsize=23);cover.text(.07,.70,'Corrected synthetic dataset v1.3 | snapshot 31 July 2026',fontsize=14,color=GRAY)
y=.60
for text in findings+model_notes:
 for ln in textwrap.wrap(text,105):cover.text(.07,y,ln,fontsize=13);y-=.035
 y-=.025
cover.text(.07,.10,'Five analysis themes, six chart sheets, auditable tables and reproducible baseline models.\nPrepared for Victoria Ekweani. Exploratory portfolio prototype; not a clinical decision tool.',fontsize=12,color=GRAY)
methodfig=plt.figure(figsize=(16,11));methodfig.text(.06,.95,'Methods, assumptions and limitations',fontsize=24,fontweight='bold');y=.88
for n,txt in enumerate(methods,1):
 lines=textwrap.wrap(f'{n}. {txt}',145)
 methodfig.text(.06,y,'\n'.join(lines),fontsize=10.1,va='top',linespacing=1.35);y-=.023*len(lines)+.019
with PdfPages(ROOT/'MedSafe_R_Chart_Report.pdf') as pdf:
 pdf.savefig(cover)
 for name,fig in pages:pdf.savefig(fig)
 pdf.savefig(methodfig)
# One self-contained offline HTML report: embedded PNGs and complete supporting tables.
sections=[]
for name,fig in pages:
 b64=base64.b64encode((ROOT/'charts'/f'{name}.png').read_bytes()).decode();sections.append(f'<section id="{name}"><h2>{html.escape(name.replace("_"," "))}</h2><img alt="{html.escape(name.replace("_"," "))} chart set; complete data tables follow" src="data:image/png;base64,{b64}"></section>')
tablehtml=''.join(f'<details><summary>{html.escape(name.replace("_"," "))}</summary><div class="table">{df.to_html(index=False,float_format=lambda x:f"{x:.4f}",border=0)}</div></details>' for name,df in tables.items() if not name.endswith('fold_predictions') and not name.endswith('oof_predictions'))
nav=''.join(f'<a href="#{name}">{html.escape(name.replace("_"," "))}</a>' for name,_ in pages)
content='<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>MedSafe-R | VictoryHealth Analytics</title><style>body{font:16px/1.6 system-ui,sans-serif;color:#18324b;background:#f1f5f8;margin:0}main{max-width:1250px;margin:auto;padding:35px 24px}h1{font-size:40px;line-height:1.15}h2{font-size:24px}nav{display:flex;flex-wrap:wrap;gap:12px}a{color:#2367a7}section,details,.intro{background:white;border-radius:12px;padding:20px;margin:24px 0}img{width:100%;height:auto}.table{overflow:auto}td,th{padding:8px;text-align:left;border-bottom:1px solid #dce5eb;white-space:nowrap}summary{cursor:pointer;font-weight:600}.badge{color:#087e83;font-weight:bold}li{margin-bottom:10px}footer{margin-top:35px}</style><main><p class="badge">VICTORYHEALTH ANALYTICS | SYNTHETIC PORTFOLIO STUDY</p><h1>MedSafe-R: reliability and safety</h1><p>Corrected v1.3 data. Snapshot 31 July 2026. All data and labels are synthetic; no clinical or deployment claims.</p><nav>'+nav+'</nav><div class="intro"><h2>Main findings</h2><ul>'+''.join('<li>'+html.escape(x)+'</li>' for x in findings+model_notes)+'</ul></div>'+''.join(sections)+'<section><h2>Methods and limitations</h2><ol>'+''.join('<li>'+html.escape(x)+'</li>' for x in methods)+'</ol></section><section><h2>Supporting tables</h2><p>Expand for exact values. All CSV tables and device-level predictions are in the accompanying package.</p>'+tablehtml+'</section><footer>Victoria Ekweani | VictoryHealth Analytics | Reproducible code and dataset included in the ZIP package.</footer></main></html>'
(ROOT/'MedSafe_R_Analysis.html').write_text(content)
(ROOT/'ANALYSIS_NOTES.md').write_text('# MedSafe-R analytical package\n\nOpen MedSafe_R_Analysis.html in a browser, or read MedSafe_R_Chart_Report.pdf. Charts are static; tables expand in the offline HTML.\n\n## Reproduce\n\n`python -m pip install -r requirements.txt`\n\n`python analysis.py`\n\nSource: data/MedSafe_R_Dataset_v1.3_cleaned.xlsx (corrected 90/365-day windows).\n\n'+ '\n\n'.join(methods)+'\n\n## Findings\n\n'+'\n\n'.join(findings+model_notes)+'\n')
print('DONE',len(pages),'chart sheets',len(tables),'tables',flush=True)
