import hashlib,json,random
import numpy as np
from sklearn.linear_model import BayesianRidge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error

def training_rows():
    rng=random.Random(32);rows=[]
    for i in range(180):
        months=rng.uniform(0,60);temp=rng.uniform(-18,22);initial=rng.uniform(80,98)
        actual=max(0,min(100,initial-.29*months-.34*(temp+18)+rng.gauss(0,2.2)))
        rows.append([round(months,4),round(temp,4),round(initial,4),round(actual,4)])
    return rows
def predict(lot,test):
    rows=training_rows();data=np.array(rows);train,hold=train_test_split(np.arange(len(rows)),test_size=.25,random_state=32)
    scaler=StandardScaler();x=scaler.fit_transform(data[train,:3]);model=BayesianRidge();model.fit(x,data[train,3]);mean,std=model.predict(scaler.transform(data[hold,:3]),return_std=True)
    value,sigma=model.predict(scaler.transform([[lot.stored_months,lot.temperature,lot.initial_rate]]),return_std=True);estimate=float(value[0]);spread=float(sigma[0]);observed=100*test.germinated/test.sampled
    return {'estimate_pct':round(estimate,3),'lower95_pct':round(max(0,estimate-1.96*spread),3),'upper95_pct':round(min(100,estimate+1.96*spread),3),'observed_pct':round(observed,3),'renewal_required':observed<85 or estimate<85,'threshold_pct':85,'holdout_mae_percentage_points':round(float(mean_absolute_error(data[hold,3],mean)),4),'holdout_interval95_coverage':round(float(np.mean((data[hold,3]>=mean-1.96*std)&(data[hold,3]<=mean+1.96*std))),4),'train_rows':len(train),'holdout_rows':len(hold),'train_indices':train.tolist(),'holdout_indices':hold.tolist(),'seed':32,'source_checksum':hashlib.sha256(json.dumps(rows,separators=(',',':')).encode()).hexdigest(),'input_snapshot':{'lot_id':lot.id,'stored_months':lot.stored_months,'temperature':lot.temperature,'initial_rate':lot.initial_rate,'sampled':test.sampled,'germinated':test.germinated},'model':'StandardScaler(train only) + BayesianRidge','interval':'Gaussian predictive mean ±1.96 predictive standard deviation, clipped to0–100'}
