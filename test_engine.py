import json
import unittest
from pathlib import Path
from types import SimpleNamespace
from engine import analyze,verify,Verification,Quote
from evaluate import evaluate
BASE=json.loads(Path(__file__).with_name('sample-company.json').read_text())
class Fake:
    def __init__(self,r): self.responses=self; self.r=r
    def parse(self,**kwargs): return SimpleNamespace(output_parsed=self.r)
class Tests(unittest.TestCase):
    def test_regression(self): self.assertTrue(all(x['match'] for x in evaluate()['cases']))
    def test_nonfinite_rejected(self):
        with self.assertRaises(ValueError): analyze({**BASE,'revenue':float('nan')})
    def test_incomparable_period_rejected(self):
        with self.assertRaises(ValueError): analyze({**BASE,'period_months':6})
    def test_zero_denominator_not_success(self):
        r=analyze({**BASE,'revenue_previous':0,'net_profit':0})
        self.assertIsNone(r['metrics']['revenue_growth']); self.assertTrue(r['data_gaps'])
    def test_demo_does_not_confirm(self):
        h=analyze(BASE)['hypotheses'][0]
        self.assertEqual(verify(h,{'doc':'应收回款全部正常'})['status'],'insufficient')
    def test_fabricated_quote_degraded(self):
        h=analyze(BASE)['hypotheses'][0]
        fake=Fake(Verification(status='supported',rationale='x',evidence=[Quote(source_id='doc',quote='not present')],remaining_requests=[]))
        self.assertEqual(verify(h,{'doc':'应收回款待核查'},'openai',fake)['status'],'insufficient')
    def test_valid_quote_still_needs_human(self):
        h=analyze(BASE)['hypotheses'][0]
        fake=Fake(Verification(status='partially_supported',rationale='待核查',evidence=[Quote(source_id='doc',quote='应收回款待核查')],remaining_requests=['流水']))
        r=verify(h,{'doc':'应收回款待核查'},'openai',fake)
        self.assertTrue(r['human_review_required']); self.assertEqual(r['status'],'partially_supported')
if __name__=='__main__': unittest.main()
