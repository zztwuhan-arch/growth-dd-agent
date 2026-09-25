import hashlib
import json
from pathlib import Path
import streamlit as st
from dotenv import load_dotenv
from engine import analyze,verify,Financials
load_dotenv()
st.set_page_config(page_title='Growth DD Agent',layout='wide')
st.title('成长型企业财务尽调 Agent')
st.caption('企业阶段 → 指标计算 → 风险假设 → 补充材料 → 证据核验 → 人工复核。产品原型，非审计或投资结论。')
mode=st.sidebar.radio('证据核验模式',['demo','openai'])
st.sidebar.caption('demo 仅检索片段；openai 会发送相关片段给模型。模型结论均待人工核验。')
sample=json.loads(Path(__file__).with_name('sample-company.json').read_text())
raw=st.text_area('公司财务数据 JSON：同币种、同单位、两个完整可比年度；比例用0–1',json.dumps(sample,ensure_ascii=False,indent=2),height=370)
st.download_button('下载输入模板',json.dumps(sample,ensure_ascii=False,indent=2),'company-template.json')
material=st.text_area('补充核查材料（默认合成资料，可替换）',Path(__file__).with_name('sample-evidence.txt').read_text(),height=160)
files=st.file_uploader('追加 UTF-8 TXT / Markdown 资料',type=['txt','md'],accept_multiple_files=True)
docs={'material':material} if material.strip() else {}
try:
    for i,f in enumerate(files): docs[f'attachment_{i+1}']=f.getvalue().decode('utf-8-sig')
except UnicodeDecodeError: st.error('资料需 UTF-8 编码'); st.stop()
key=hashlib.sha256(json.dumps([raw,docs,mode],ensure_ascii=False).encode()).hexdigest()
if st.session_state.get('input_key')!=key:
    st.session_state.pop('report',None); st.session_state.pop('human',None)
if st.button('运行尽调工作流',type='primary'):
    try:
        if len(docs)>10 or any(len(v)>100000 for v in docs.values()): raise ValueError('最多10份材料，每份10万字符')
        report=analyze(json.loads(raw))
        with st.spinner('计算指标并核查材料…'):
            for h in report['hypotheses']: h['verification']=verify(h,docs,mode)
        st.session_state['report']=report; st.session_state['input_key']=key
    except (ValueError,RuntimeError) as e: st.error(str(e))
r=st.session_state.get('report')
if r:
    st.subheader('指标与风险假设')
    st.json(r['metrics'])
    if r['data_gaps']: st.warning('; '.join(r['data_gaps']))
    if not r['hypotheses']: st.info('未触发本原型阈值，不代表没有风险。')
    for h in r['hypotheses']:
        with st.expander(h['title'],expanded=True):
            st.write(h['hypothesis']); st.write('需补材料：'+'；'.join(h['material_requests']))
            st.write('核验状态：'+h['verification']['status'])
            st.write(h['verification']['rationale'])
            st.json(h['verification']['candidate_snippets'])
    with st.form('human'):
        decision=st.selectbox('人工复核',['继续补充核查','调整风险假设','归档本轮核查'])
        note=st.text_area('复核依据与下一步')
        if st.form_submit_button('记录复核'):
            if note.strip(): st.session_state['human']={'decision':decision,'note':note}
            else: st.error('请填写复核依据')
    human=st.session_state.get('human')
    if human: st.success('已记录：'+human['decision'])
    st.download_button('下载工作流记录',json.dumps({**r,'human_review':human},ensure_ascii=False,indent=2),'diligence-report.json','application/json')
    st.caption('结果仅留在当前会话，需留档请下载。资料真实性、完整性和解释仍需专业人员核实。')
