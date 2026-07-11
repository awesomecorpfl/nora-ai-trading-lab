import json,sys
from html.parser import HTMLParser
from pathlib import Path
class P(HTMLParser):
 def __init__(s):super().__init__();s.rows=[];s.row=[];s.cell=[];s.incell=False
 def handle_starttag(s,t,a):
  if t=='tr':s.row=[]
  if t in ('td','th'):s.incell=True;s.cell=[]
 def handle_data(s,d):
  if s.incell:s.cell.append(d.strip())
 def handle_endtag(s,t):
  if t in ('td','th'):s.row.append(' '.join(x for x in s.cell if x));s.incell=False
  if t=='tr' and s.row:s.rows.append(s.row)
def parse(x):
 p=P();p.feed(Path(x).read_text(encoding='utf-16'));rows=p.rows;start=next(i for i,r in enumerate(rows) if r==['Deals']);hdr=rows[start+1];deals=[]
 for r in rows[start+2:]:
  if r==['Orders'] or len(r)!=len(hdr):break
  deals.append(dict(zip(hdr,r)))
 metrics={r[0].rstrip(':'):r[1] for r in rows if len(r)==2 and r[0].endswith(':')}
 return {'metrics':metrics,'deals':deals}
a,b=map(parse,sys.argv[1:3]);same=a==b;Path(sys.argv[3]).write_text(json.dumps({'equal':same,'normalization':'none; native report generation metadata is not parsed','run1':a,'run2':b},indent=2));raise SystemExit(0 if same else 2)
