import streamlit as st
import os
import openai as ai
from PyPDF2 import PdfReader

# ai.api_key = st.secrets["openai_key"]
ai.api_key = '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'

st.markdown("""
# 📝 생성형AI 기반 자기소개서 생성기

자기소개서를 제작하기 위한 단계:
1. 이력서를 업로드 하거나, 텍스트로 복사/붙여넣기를 해주세요
2. 직무 소개서를 복사/붙여넣기 해주세요
3. 지원자가 추가로 넣고 싶은 정보들을 입력해주세요
"""
)

# radio for upload or copy paste option         
res_format = st.radio(
    "이력서 업로드 혹은 텍스트로 붙여넣기",
    ('Upload', 'Paste'))

if res_format == 'Upload':
    # upload_resume
    res_file = st.file_uploader('📁 pdf 형식 이력서를 업로드 해주세요!')
    if res_file:
        pdf_reader = PdfReader(res_file)

        # Collect text from pdf
        res_text = ""
        for page in pdf_reader.pages:
            res_text += page.extract_text()
else:
    # use the pasted contents instead
    res_text = st.text_input('Pasted resume elements')

with st.form('input_form'):
    # other inputs
    job_desc = st.text_input('직무 소개서')
    user_name = st.text_input('지원자 이름')
    company = st.text_input('회사 이름')
    # manager = st.text_input('Hiring manager')
    role = st.text_input('직무명')
    referral = st.text_input('해당 이력서를 찾은 경로')
    ai_temp = st.number_input('AI Temperature (0.0-1.0) Input how creative the API can be',value=.99)

    # submit button
    submitted = st.form_submit_button("자기소개서 생성하기")

# if the form is submitted run the openai completion   
if submitted:

    # note that the ChatCompletion is used as it was found to be more effective to produce good results
    # using just Completion often resulted in exceeding token limits
    # according to https://platform.openai.com/docs/models/gpt-3-5
    # Our most capable and cost effective model in the GPT-3.5 family is gpt-3.5-turbo which has been optimized for chat 
    # but works well for traditional completions tasks as well.

    completion = ai.ChatCompletion.create(
      #model="gpt-3.5-turbo-16k", 
      model = "gpt-3.5-turbo",
      temperature=ai_temp,
      messages = [
        {"role": "user", "content" : f"You will need to generate a cover letter based on specific resume and a job description"},
        {"role": "user", "content" : f"My resume text: {res_text}"},
        {"role": "user", "content" : f"The job description is: {job_desc}"},
        {"role": "user", "content" : f"The candidate's name to include on the cover letter: {user_name}"},
        {"role": "user", "content" : f"The job title/role : {role}"},
        # {"role": "user", "content" : f"The hiring manager is: {manager}"},
        {"role": "user", "content" : f"How you heard about the opportunity: {referral}"},
        {"role": "user", "content" : f"The company to which you are generating the cover letter for: {company}"},
        {"role": "user", "content" : f"The cover letter should have three content paragraphs"},
        {"role": "user", "content" : f""" 
        In the first paragraph focus on the following: you will convey who you are, what position you are interested in, and where you heard
        about it, and summarize what you have to offer based on the above resume
        """},
            {"role": "user", "content" : f""" 
        In the second paragraph focus on why the candidate is a great fit drawing parallels between the experience included in the resume 
        and the qualifications on the job description.
        """},
                {"role": "user", "content" : f""" 
        In the 3RD PARAGRAPH: Conclusion
        Restate your interest in the organization and/or job and summarize what you have to offer and thank the reader for their time and consideration.
        """},
        {"role": "user", "content" : f""" 
        note that contact information may be found in the included resume text and use and/or summarize specific resume context for the letter
            """},
        {"role": "user", "content" : f"Use {user_name} as the candidate"},
        
        {"role": "user", "content" : f"Generate a specific cover letter based on the above. Generate the response and include appropriate spacing between the paragraph text"},
        
        {"role": "user", "content" : f"You must write down this cover letter in Korean. "},

      ]
    )

    response_out = completion['choices'][0]['message']['content']
    st.write(response_out)

    # include an option to download a txt file
    st.download_button('Download the cover_letter', response_out)