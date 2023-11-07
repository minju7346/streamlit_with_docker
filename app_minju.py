import streamlit as st
import os
import openai as ai
from PyPDF2 import PdfReader

import os
import pymysql

from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.llms import OpenAI
from langchain.chains import RetrievalQA
from langchain.document_loaders import TextLoader
from langchain.document_loaders import DirectoryLoader
from langchain.prompts import ChatPromptTemplate
from langchain.prompts.chat import SystemMessage, HumanMessagePromptTemplate
from langchain.chat_models import ChatOpenAI


# ai.api_key = st.secrets["openai_key"]
ai.api_key = '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'

db_config = {
    'host': 'recruit.cob9hpevtink.ap-northeast-2.rds.amazonaws.com',
    'database': 'new_schema',
    'port': 3306,
    'user': 'admin',
    'password': '201912343'
}

# 데이터베이스 연결
db = pymysql.connect(**db_config)
cursor = db.cursor()

# 폴더 경로 생성
output_folder = 'txt_data'
os.makedirs(output_folder, exist_ok=True)

try:
    # 고유한 corp_name 값 가져오기
    sql = 'SELECT DISTINCT corp_name FROM recuity'
    cursor.execute(sql)
    
    corp_names = cursor.fetchall()
    
    for corp_name in corp_names:
        # 각 corp_name에 대한 TXT 파일 경로 생성
        txt_file_name = os.path.join(output_folder, f'{corp_name[0]}.txt')
        
        # SQL 쿼리 실행 (해당 corp_name을 가진 행을 가져옴)
        sql = f'SELECT * FROM recuity WHERE corp_name = %s'
        cursor.execute(sql, (corp_name[0],))
        
        # 결과를 TXT 파일로 저장
        with open(txt_file_name, 'w', encoding='utf-8') as txt_file:
            # Get the column names
            column_names = [desc[0] for desc in cursor.description]
            txt_file.write(', '.join(column_names) + '\n')
            
            result = cursor.fetchall()
            for row in result:
                # Write column names and corresponding data values
                for col_name, data in zip(column_names, row):
                    txt_file.write(f'{col_name}: {data}\n')
                txt_file.write('\n')  # 각 회사 데이터 구분을 위한 줄 바꿈 추가

finally:
    # 데이터베이스 연결 닫기
    db.close()
    
loader = DirectoryLoader('./txt_data', glob='*.txt', loader_cls=TextLoader)
documents = loader.load()

text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200) #1000자 씩 끊되, 200자 씩 겹치게 만든다.
texts = text_splitter.split_documents(documents)

os.environ['OPENAI_API_KEY'] = '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'

persist_directory='db'

embedding = OpenAIEmbeddings()

vectordb = Chroma.from_documents(
    documents=texts,
    embedding=embedding,
    persist_directory=persist_directory
)
vectordb.persist() # 초기화
vectordb=None

vectordb = Chroma( # 기존 벡터 DB 로드
    persist_directory=persist_directory,
    embedding_function=embedding
)

retriever = vectordb.as_retriever(search_kwargs={"k": 3}) # 유사도 상위 3개만 반환

docs = retriever.get_relevant_documents("재택근무, 유연 근무제")

source_list = []

for doc in docs:
    source = doc.metadata["source"]
    cleaned_source = source.replace("txt_data/", "").replace(".txt", "")
    source_list.append(cleaned_source)


text = ""

# source_list에 있는 각 기업명에 대하여
for source in source_list:
    # 파일명을 생성합니다.
    file_name = f"txt_data/{source}.txt"
    
    # 파일을 읽고 내용을 text 변수에 추가합니다.
    with open(file_name, 'r', encoding='utf-8') as f:
        text += f.read()

tab1, tab2= st.tabs(['회사 찾기', '자소서 쓰기'])

with tab1:
    st.markdown("""
    # 📝 본인이 원하는 스타트업의 분위기를 선택해주세요
    
    성향에 맞는 스타트업을 추천해드립니다.
    """
    )
    
    options = st.multiselect(
    '자신의 원하는 스타트업의 핵심가치를 모두 선택해주세요',
    ['편한 복장', '자유로운 소통', '훌륭한 동료', '성장 가능성이 있는', '워라밸이 보장된', '자율재택근무', '탄탄한 비즈니스모델', '개발 능력 향상'],
    default=['편한 복장'])
    
    str_options = ', '.join(options)

    retriever = vectordb.as_retriever(search_kwargs={"k": 3})
    
    docs = retriever.get_relevant_documents(str_options)
    
    source_list = []

    for doc in docs:
        source = doc.metadata["source"]
        cleaned_source = source.replace("txt_data/", "").replace(".txt", "")
        source_list.append(cleaned_source)
        
    for i, source in enumerate(source_list):
        if st.button(source, key=f'button_{i}'):  # 고유한 키 할당
            st.write(source)
        
    
with tab2: 
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
        question1 = st.text_input('자기소개서 문항 1')
        question2 = st.text_input('자기소개서 문항 2')
        question3 = st.text_input('자기소개서 문항 3')
        ai_temp = st.number_input('AI Temperature (0.0-1.0) Input how creative the API can be',value=.99)

        # submit button
        submitted = st.form_submit_button("자기소개서 생성하기")

    # if the form is submitted run the openai completion   
    if submitted:
        
        template = ChatPromptTemplate.from_messages(
        [
            SystemMessage(
                content=(
                    f"""
                    Write me the resume for {company} in Korean.
                    My resume text: {res_text},
                    
                    There are 3 questions for the resume that you should answer.
                    1. {question1}, in just one paragraph
                    2. {question2}, in just one paragraph
                    3. {question3}, in just one paragraph
                    
                    - Tone : Humble
                    - Style : MECE, accurate
                    - Reader level : New employee
                    - Perspective : Recruiter
                    - Format : markdown
                    
                    You MUST answer in Korean. 
                    """
                )
            ),
            HumanMessagePromptTemplate.from_template("{text}"),
        ])

        llm = ChatOpenAI(model="gpt-3.5-turbo-16k")

        answer = llm(template.format_messages(text=text)).content

        # note that the ChatCompletion is used as it was found to be more effective to produce good results
        # using just Completion often resulted in exceeding token limits
        # according to https://platform.openai.com/docs/models/gpt-3-5
        # Our most capable and cost effective model in the GPT-3.5 family is gpt-3.5-turbo which has been optimized for chat 
        # but works well for traditional completions tasks as well.

        # completion = ai.ChatCompletion.create(
        #   #model="gpt-3.5-turbo-16k", 
        #   model = "gpt-3.5-turbo",
        #   temperature=ai_temp,
        #   messages = [
        #     {"role": "user", "content" : f"You will need to generate a cover letter based on specific resume and a job description"},
        #     {"role": "user", "content" : f"My resume text: {res_text}"},
        #     {"role": "user", "content" : f"The job description is: {job_desc}"},
        #     {"role": "user", "content" : f"The candidate's name to include on the cover letter: {user_name}"},
        #     {"role": "user", "content" : f"The job title/role : {role}"},
        #     # {"role": "user", "content" : f"The hiring manager is: {manager}"},
        #     {"role": "user", "content" : f"How you heard about the opportunity: {referral}"},
        #     {"role": "user", "content" : f"The company to which you are generating the cover letter for: {company}"},
        #     {"role": "user", "content" : f"The cover letter should have three content paragraphs"},
        #     {"role": "user", "content" : f""" 
        #     In the first paragraph focus on the following: you will convey who you are, what position you are interested in, and where you heard
        #     about it, and summarize what you have to offer based on the above resume
        #     """},
        #         {"role": "user", "content" : f""" 
        #     In the second paragraph focus on why the candidate is a great fit drawing parallels between the experience included in the resume 
        #     and the qualifications on the job description.
        #     """},
        #             {"role": "user", "content" : f""" 
        #     In the 3RD PARAGRAPH: Conclusion
        #     Restate your interest in the organization and/or job and summarize what you have to offer and thank the reader for their time and consideration.
        #     """},
        #     {"role": "user", "content" : f""" 
        #     note that contact information may be found in the included resume text and use and/or summarize specific resume context for the letter
        #         """},
        #     {"role": "user", "content" : f"Use {user_name} as the candidate"},
            
        #     {"role": "user", "content" : f"Generate a specific cover letter based on the above. Generate the response and include appropriate spacing between the paragraph text"},
            
        #     {"role": "user", "content" : f"You must write down this cover letter in Korean. "},

        #   ]
        # )

        # response_out = completion['choices'][0]['message']['content']
        
        
        st.write(answer)

        # include an option to download a txt file
        st.download_button('Download the cover_letter', answer)