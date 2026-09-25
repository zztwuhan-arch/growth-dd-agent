import json
from pathlib import Path
from engine import analyze

def evaluate():
    cases=json.loads(Path(__file__).with_name('evaluation-cases.json').read_text())
    tp=fp=fn=0; rows=[]
    for case in cases:
        predicted={h['id'] for h in analyze(case['input'])['hypotheses']}; expected=set(case['expected'])
        tp+=len(predicted&expected); fp+=len(predicted-expected); fn+=len(expected-predicted)
        rows.append({'id':case['id'],'match':predicted==expected})
    return {'scope':'12 synthetic regression cases; rule consistency, not real-world accuracy',
            'micro_precision':tp/(tp+fp) if tp+fp else None,'micro_recall':tp/(tp+fn) if tp+fn else None,
            'true_positive':tp,'false_positive':fp,'false_negative':fn,'cases':rows}
if __name__=='__main__': print(json.dumps(evaluate(),ensure_ascii=False,indent=2))
