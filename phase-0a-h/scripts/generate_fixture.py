#!/usr/bin/env python3
import csv, hashlib, sys
from datetime import datetime, timedelta, timezone
p=sys.argv[1]; start=datetime(2024,1,2,0,0,tzinfo=timezone.utc)
with open(p,'w',newline='') as f:
 w=csv.writer(f);w.writerow(['time','open','high','low','close','tick_volume','spread','real_volume'])
 for i in range(12):
  x=100+i;w.writerow([(start+timedelta(minutes=i)).strftime('%Y.%m.%d %H:%M'),x,x+0.5,x-0.2,x+0.25,10,1,0])
print(hashlib.sha256(open(p,'rb').read()).hexdigest())
