# 그룹바이
import json
import pandas as pd
import pymysql



# DB 접근을 위한 전역 변수들
host_name = 'localhost'#'junggoheaven-rds.cd20g22ic9fp.ap-northeast-2.rds.amazonaws.com'
host_port = 3306
username = 'zen'#'admin'
password = '1234!@abcABC'#'junggoheaven!'
database_name = 'junggoheaven'#'JungGoHeaven'

db = pymysql.connect(
    host = host_name,     # MySQL 서버 주소
    port = host_port,     # MySQL 서버 포트
    user = username,      # 사용자 이름
    passwd = password,    # 사용자 비밀번호
    db = database_name,   # 사용할 데이터 베이스 스키마 이름
    charset = 'utf8'
)

query = "SELECT gender, location, age_group, product_id, product_category FROM product_bespoke_info"
#df = pd.read_sql(SQL, db)




def groupby(request_data):

    gender = request_data['gender']
    location = request_data['location']
    age_group = request_data['ageGroup']

    #df = pd.read_csv('/home/zen35/Documents/jupyternotebook/5050.csv')

    df = pd.read_sql(query, db)

    popular_products = (
        df.groupby(['gender', 'location', 'age_group', 'product_id', 'product_category'])
        .size()
        .reset_index(name='count')
    )

    top_products = (
        popular_products
        .sort_values(['gender', 'location', 'age_group', 'count'], ascending=[True, True, True, False])
        .drop_duplicates(['gender', 'location', 'age_group'])
    )

    match = top_products[
        (top_products['gender'] == gender) &
        (top_products['location'] == location) &
        (top_products['age_group'] == age_group)
    ]
    if not match.empty:
        return match[['product_id', 'product_category']].iloc[0].to_dict()
    else:
        return {'ERROR': '추천 데이터 오류 관리자에게 문의하세요'}













# 랜덤포레스트
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split


def bespoke_product_category(request_data):
    gender = request_data['gender']
    location = request_data['location']
    age_group = request_data['ageGroup']

    # 데이터적재
    #df = pd.read_csv("/home/zen35/Documents/jupyternotebook/sampledata3.csv")

    df = pd.read_sql(query, db)

    # 특성타겟정의
    # X = df[['gender', 'location', 'age_group']]
    # y = df['product_category']  # product_id

    X = df[['gender', 'location', 'age_group']]
    y = df['product_category']  # product_id

    # 학습 테스트 셋 분리
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, train_size=0.8, random_state=42)

    # 모델학습
    model = RandomForestClassifier(
        n_estimators=300,  # 트리갯수
        max_depth=10,  # 과적합방지
        min_samples_split=5,  # 가지치기 기준 완화
        min_samples_leaf=2,  # 너무적은샘플 피하기
        max_features='sqrt',  # 특성선택전략
        random_state=42,
        class_weight='balanced')

    model.fit(X_train, y_train)


    user_input = pd.DataFrame([[gender, location, age_group]],
                             columns=['gender', 'location', 'age_group'])

    proba = model.predict_proba(user_input)[0]
    category_probs = dict(zip(model.classes_, proba))

    # 최상위 상품 카테고리 3개
    top_n = 3
    top_categories = sorted(category_probs.items(), key=lambda x: x[1], reverse=True)[:top_n]


    return json.dumps(top_categories, default=str) # json 래핑






# 플라스크 실행
from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route('/mlserver', methods = ['POST'])
def home():

    request_data = request.get_json() # Spring에서 부터 온 json데이터 역직렬화

    print(request_data) # 역직렬화 데이터 보기


    #return groupby(request_data)

    return bespoke_product_category(request_data)


if __name__ == '__main__':
   app.run('0.0.0.0', port = 5000, debug = True)
