<<<<<<< Updated upstream
import csv
import re
import time
import requests
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from math import radians, cos, sin, asin, sqrt

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hospital.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class Hospital(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    holiday_service = db.Column(db.Boolean, default=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'address': self.address,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'holiday_service': self.holiday_service,
        }

def clean_address_strict(address):
    # 괄호 안 내용 제거
    address = re.sub(r'\([^)]*\)', '', address)
    # 콤마 및 그 뒤 내용 제거 (층, 호, 동 등 세부 주소 정보)
    address = re.sub(r',.*$', '', address)
    # 숫자+단위(층, 호, 동) 통째로 제거 (' 2층', '302호' 등)
    address = re.sub(r'\s*\d+(층|호|동)', '', address)
    # 남은 쉼표는 공백으로 대체
    address = address.replace(',', ' ')
    # 중복 공백 하나로 축소 및 양끝 공백 제거
    address = re.sub(r'\s+', ' ', address).strip()
    return address

def get_lat_lng_nominatim(address):
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        'q': address,
        'format': 'json',
        'limit': 1,
    }
    headers = {
        'User-Agent': 'MyHolidayHospitalApp/1.0 (sylee02@dankook.ac.kr)'
    }
    response = requests.get(url, params=params, headers=headers)
    response.raise_for_status()
    data = response.json()
    if not data:
        raise Exception(f"주소 좌표를 찾을 수 없음: {address}")
    return float(data[0]['lat']), float(data[0]['lon'])

def load_csv_to_db(path):
    with open(path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        success_count = 0
        fail_count = 0
        for row in reader:
            raw_addr = row['주소']
            cleaned_addr = clean_address_strict(raw_addr)
            try:
                lat, lng = get_lat_lng_nominatim(cleaned_addr)
            except Exception as e:
                print(f"지오코딩 실패: '{raw_addr}' -> '{cleaned_addr}' / 이유: {e}")
                fail_count += 1
                continue
            hospital = Hospital(
                name=row['의료기관명'],
                address=cleaned_addr,
                latitude=lat,
                longitude=lng,
                holiday_service=True,
            )
            db.session.add(hospital)
            success_count += 1
            time.sleep(1)  # 호출 속도 제한
        db.session.commit()
        print(f"지오코딩 성공: {success_count}건, 실패: {fail_count}건")

def haversine(lon1, lat1, lon2, lat2):
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1)*cos(lat2)*sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    return 6371 * c

@app.route('/api/holiday_hospitals', methods=['GET'])
def api_holiday_hospitals():
    try:
        lat = float(request.args.get('lat'))
        lng = float(request.args.get('lng'))
        radius = float(request.args.get('radius', 5))
    except (TypeError, ValueError):
        return jsonify({'error': 'lat, lng 쿼리 필수'}), 400

    hospitals = Hospital.query.filter_by(holiday_service=True).all()
    nearby = []
    for h in hospitals:
        dist = haversine(lng, lat, h.longitude, h.latitude)
        if dist <= radius:
            d = h.to_dict()
            d['distance_km'] = round(dist, 2)
            nearby.append(d)
    nearby.sort(key=lambda x: x['distance_km'])
    return jsonify(nearby)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if Hospital.query.count() == 0:
            print("CSV 읽고 주소 전처리 + 지오코딩 시작...")
            load_csv_to_db('평일 야간 휴일 의료기관 현황.csv')
            print("데이터 적재 완료!")
    app.run(debug=True)
=======
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from math import radians, cos, sin, asin, sqrt
import csv

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hospital.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# ──────────────────────────────────────────────────────────────────────────
#  Hospital 모델 (종별코드 / 종별코드명 추가 → 의원/병원/종합병원 구분용)
# ──────────────────────────────────────────────────────────────────────────
class Hospital(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    department_code = db.Column(db.String(10), nullable=False)
    department_name = db.Column(db.String(100))
    facility_code = db.Column(db.String(10))    
    facility_name = db.Column(db.String(50))      
    phone = db.Column(db.String(50))
    mon_hours = db.Column(db.String(50))
    tue_hours = db.Column(db.String(50))
    wed_hours = db.Column(db.String(50))
    thu_hours = db.Column(db.String(50))
    fri_hours = db.Column(db.String(50))
    sat_hours = db.Column(db.String(50))
    sun_hours = db.Column(db.String(50))

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'department_code': self.department_code,
            'department_name': self.department_name,
            'facility_code': self.facility_code,
            'facility_name': self.facility_name,
            'phone': self.phone,
            'mon_hours': self.mon_hours,
            'tue_hours': self.tue_hours,
            'wed_hours': self.wed_hours,
            'thu_hours': self.thu_hours,
            'fri_hours': self.fri_hours,
            'sat_hours': self.sat_hours,
            'sun_hours': self.sun_hours,
        }


HIGH_TIER_FACILITY_CODES = {'1', '11', '21'}   # 상급종합, 종합병원, 병원


def load_csv_to_db(filepath):
    """hospital_info2.csv (종별코드 포함 버전)을 읽어 DB에 적재"""
    Hospital.query.delete()
    db.session.commit()

    with open(filepath, newline='', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile)
        count = 0
        for row in reader:
            lat_str = (row.get('병원 좌표(y)') or '').strip()
            lng_str = (row.get('병원 좌표(x)') or '').strip()

            if not lat_str or not lng_str:
                continue

            hospital = Hospital(
                name=row.get('병원 이름', '').strip(),
                department_code=str(row.get('진료과목코드', '')).strip(),
                department_name=row.get('진료 과목', '').strip(),
                facility_code=str(row.get('종별코드', '')).strip(),
                facility_name=row.get('종별코드명', '').strip(),
                phone=row.get('병원 전화번호', '').strip(),
                latitude=float(lat_str),
                longitude=float(lng_str),
                mon_hours=row.get('월요일 운영시간', '').strip(),
                tue_hours=row.get('화요일 운영시간', '').strip(),
                wed_hours=row.get('수요일 운영시간', '').strip(),
                thu_hours=row.get('목요일 운영시간', '').strip(),
                fri_hours=row.get('금요일 운영시간', '').strip(),
                sat_hours=row.get('토요일 운영시간', '').strip(),
                sun_hours=row.get('일요일 운영시간', '').strip(),
            )
            db.session.add(hospital)
            count += 1
            if count % 5000 == 0:
                db.session.commit()
        db.session.commit()
        print(f"{count}개 병원 데이터 적재")


# ──────────────────────────────────────────────────────────────────────────
#  1차 증상 (사용자가 다중 선택 가능)
# ──────────────────────────────────────────────────────────────────────────
primary_symptoms = [
    "감기", "기침", "콧물", "발열", "두통", "어지럼증", "기억력 저하", "불면증",
    "우울감", "불안", "복통", "설사", "변비", "구토", "속쓰림", "가슴 통증",
    "두근거림", "호흡 곤란", "허리 통증", "목 통증", "어깨 통증", "무릎 통증",
    "손목 통증", "손발 저림", "마비 증상", "눈 통증", "시력 저하", "눈 건조",
    "귀 통증", "귀 먹먹함", "코막힘", "목 붓기", "쉰 목소리", "피부 가려움",
    "여드름", "탈모", "사마귀", "화상", "상처", "멍울", "생리통", "질 분비물 이상",
    "임신 의심", "갱년기 증상", "소변 통증", "야간뇨", "요실금", "치통", "턱관절 통증",
    "입냄새", "만성 피로", "체중 감소", "체중 증가", "수족냉증", "잦은 감기", "건강검진 상담"
]

HIGH_RISK_SYMPTOMS = {"호흡 곤란", "가슴 통증", "마비 증상", "두근거림"}

# ──────────────────────────────────────────────────────────────────────────
#  1차 증상 → 추정 질환(2차 후보) 1:N 매핑
# ──────────────────────────────────────────────────────────────────────────
symptom_conditions = {
    "감기": ["단순 감기", "독감", "코로나19 의심", "알레르기성 비염"],
    "기침": ["단순 감기", "독감", "알레르기성 비염", "기관지염", "폐렴"],
    "콧물": ["단순 감기", "독감", "알레르기성 비염", "코로나19 의심"],
    "발열": ["단순 감기", "독감", "코로나19 의심", "장염", "폐렴", "요로감염"],
    "두통": ["편두통", "긴장성 두통", "고혈압 의심", "뇌질환 의심"],
    "어지럼증": ["이석증", "빈혈", "기립성 저혈압", "뇌질환 의심"],
    "기억력 저하": ["경도인지장애", "치매 의심", "우울증"],
    "불면증": ["불면증", "스트레스성 수면장애", "갑상선기능 이상"],
    "우울감": ["우울증", "적응장애", "갑상선기능 이상", "만성 피로"],
    "불안": ["불안장애", "공황장애", "갑상선기능 이상"],
    "복통": ["급성 위장염", "과민성대장증후군", "역류성 식도염", "담석 의심", "맹장염 의심"],
    "설사": ["급성 장염", "식중독", "과민성대장증후군"],
    "변비": ["과민성대장증후군", "대장운동저하"],
    "구토": ["급성 장염", "식중독", "위염", "뇌압 상승 의심"],
    "속쓰림": ["역류성 식도염", "위염", "위궤양"],
    "가슴 통증": ["역류성 식도염", "협심증 의심", "늑간신경통", "공황장애"],
    "두근거림": ["부정맥 의심", "갑상선기능 이상", "공황장애"],
    "호흡 곤란": ["천식", "폐렴", "심부전 의심", "공황장애", "코로나19 의심"],
    "허리 통증": ["근육통(요추부 염좌)", "허리디스크", "척추관협착증"],
    "목 통증": ["근육통(경추부 염좌)", "목디스크", "거북목증후군"],
    "어깨 통증": ["회전근개손상", "오십견", "근막통증증후군"],
    "무릎 통증": ["퇴행성 관절염", "십자인대손상", "연골손상"],
    "손목 통증": ["손목터널증후군", "건초염", "손목 인대손상"],
    "손발 저림": ["허리디스크", "손목터널증후군", "말초신경병증", "혈액순환장애"],
    "마비 증상": ["뇌졸중 의심", "말초신경병증", "디스크에 의한 신경압박"],
    "눈 통증": ["결막염", "각막손상", "녹내장 의심"],
    "시력 저하": ["굴절이상", "백내장", "녹내장 의심", "당뇨망막병증 의심"],
    "눈 건조": ["안구건조증", "결막염"],
    "귀 통증": ["중이염", "외이도염"],
    "귀 먹먹함": ["중이염", "이관기능장애", "돌발성 난청 의심"],
    "코막힘": ["알레르기성 비염", "축농증", "단순 감기"],
    "목 붓기": ["편도염", "갑상선 질환 의심"],
    "쉰 목소리": ["후두염", "성대결절", "역류성 식도염"],
    "피부 가려움": ["접촉성 피부염", "아토피", "두드러기", "건선"],
    "여드름": ["여드름성 피부염", "모낭염"],
    "탈모": ["남성형 탈모", "원형 탈모", "휴지기 탈모"],
    "사마귀": ["바이러스성 사마귀", "티눈"],
    "화상": ["경증 화상", "중증 화상"],
    "상처": ["단순 열상", "감염 우려 상처"],
    "멍울": ["피지낭종", "유방 멍울 의심", "임파선염"],
    "생리통": ["원발성 월경통", "자궁내막증 의심", "골반염 의심"],
    "질 분비물 이상": ["질염", "골반염 의심"],
    "임신 의심": ["임신 초기 확인 필요"],
    "갱년기 증상": ["갱년기 증후군"],
    "소변 통증": ["방광염", "요로감염", "요로결석 의심"],
    "야간뇨": ["방광 과민증", "전립선비대증 의심"],
    "요실금": ["복압성 요실금", "과민성 방광"],
    "치통": ["충치", "치주염"],
    "턱관절 통증": ["턱관절장애"],
    "입냄새": ["치주질환", "구강건조증"],
    "만성 피로": ["피로증후군", "갑상선기능 이상", "빈혈", "수면장애"],
    "체중 감소": ["갑상선기능 이상", "당뇨 의심", "소화기 질환 의심"],
    "체중 증가": ["갑상선기능 이상", "대사증후군"],
    "수족냉증": ["말초혈액순환장애", "갑상선기능 이상", "레이노증후군 의심"],
    "잦은 감기": ["면역력 저하", "만성 비염", "알레르기성 비염"],
    "건강검진 상담": ["건강검진 결과 상담"],
}

# ──────────────────────────────────────────────────────────────────────────
#  질환(2차 후보) → 진료과목코드
# ──────────────────────────────────────────────────────────────────────────
condition_departments = {
    "단순 감기": ["1"], "독감": ["1"], "코로나19 의심": ["1", "24"],
    "알레르기성 비염": ["13"], "기관지염": ["1", "7"], "폐렴": ["1", "7", "24"],
    "장염": ["1"], "요로감염": ["15"],
    "편두통": ["2"], "긴장성 두통": ["2", "21"], "고혈압 의심": ["1"],
    "뇌질환 의심": ["6", "24"], "이석증": ["13", "2"], "빈혈": ["1"],
    "기립성 저혈압": ["1", "2"],
    "경도인지장애": ["2", "3"], "치매 의심": ["2", "24"], "우울증": ["3"],
    "불면증": ["3"], "스트레스성 수면장애": ["3"], "갑상선기능 이상": ["1"],
    "적응장애": ["3"], "만성 피로": ["23", "1"], "불안장애": ["3"], "공황장애": ["3"],
    "급성 위장염": ["1"], "과민성대장증후군": ["1"], "역류성 식도염": ["1"],
    "담석 의심": ["4", "1"], "맹장염 의심": ["4", "24"],
    "급성 장염": ["1"], "식중독": ["1", "24"], "대장운동저하": ["1"],
    "위염": ["1"], "뇌압 상승 의심": ["6", "24"], "위궤양": ["1"],
    "협심증 의심": ["1", "24"], "늑간신경통": ["5", "21"],
    "부정맥 의심": ["1", "24"], "천식": ["1", "7"], "심부전 의심": ["1", "24"],
    "근육통(요추부 염좌)": ["5", "21"], "허리디스크": ["6", "5", "21"],
    "척추관협착증": ["6", "5"], "근육통(경추부 염좌)": ["5", "21"],
    "목디스크": ["6", "5"], "거북목증후군": ["21", "5"],
    "회전근개손상": ["5"], "오십견": ["5", "21"], "근막통증증후군": ["21", "5"],
    "퇴행성 관절염": ["5"], "십자인대손상": ["5"], "연골손상": ["5"],
    "손목터널증후군": ["5", "6"], "건초염": ["5"], "손목 인대손상": ["5"],
    "말초신경병증": ["2", "6"], "혈액순환장애": ["1", "2"],
    "뇌졸중 의심": ["6", "24"], "디스크에 의한 신경압박": ["6", "5"],
    "결막염": ["12"], "각막손상": ["12", "24"], "녹내장 의심": ["12"],
    "굴절이상": ["12"], "백내장": ["12"], "당뇨망막병증 의심": ["12", "1"],
    "안구건조증": ["12"],
    "중이염": ["13"], "외이도염": ["13"], "이관기능장애": ["13"],
    "돌발성 난청 의심": ["13", "24"], "축농증": ["13"], "편도염": ["13"],
    "갑상선 질환 의심": ["1"], "후두염": ["13"], "성대결절": ["13"],
    "접촉성 피부염": ["14"], "아토피": ["14"], "두드러기": ["14", "24"],
    "건선": ["14"], "여드름성 피부염": ["14"], "모낭염": ["14"],
    "남성형 탈모": ["14"], "원형 탈모": ["14"], "휴지기 탈모": ["14"],
    "바이러스성 사마귀": ["14"], "티눈": ["14"],
    "경증 화상": ["8", "14"], "중증 화상": ["8", "24"],
    "단순 열상": ["4", "8"], "감염 우려 상처": ["4", "24"],
    "피지낭종": ["8", "14"], "유방 멍울 의심": ["4"], "임파선염": ["4", "1"],
    "원발성 월경통": ["10"], "자궁내막증 의심": ["10"], "골반염 의심": ["10", "24"],
    "질염": ["10"], "임신 초기 확인 필요": ["10"], "갱년기 증후군": ["10"],
    "방광염": ["15"], "요로결석 의심": ["15", "24"], "방광 과민증": ["15"],
    "전립선비대증 의심": ["15"], "복압성 요실금": ["15"], "과민성 방광": ["15"],
    "충치": ["49"], "치주염": ["49"], "턱관절장애": ["49"],
    "치주질환": ["49"], "구강건조증": ["49"],
    "피로증후군": ["23", "1"], "수면장애": ["3"], "당뇨 의심": ["1"],
    "소화기 질환 의심": ["1"], "대사증후군": ["1", "23"],
    "말초혈액순환장애": ["1", "2"], "레이노증후군 의심": ["1", "2"],
    "면역력 저하": ["1", "23"], "만성 비염": ["13"],
    "건강검진 결과 상담": ["23"],
}

# 질환명 자체가 응급/고위험 신호인 경우
HIGH_RISK_CONDITIONS = {
    "코로나19 의심", "폐렴", "뇌질환 의심", "치매 의심", "맹장염 의심",
    "뇌압 상승 의심", "협심증 의심", "부정맥 의심", "심부전 의심",
    "뇌졸중 의심", "각막손상", "돌발성 난청 의심", "두드러기",
    "중증 화상", "감염 우려 상처", "골반염 의심", "요로결석 의심", "식중독",
}

DEPARTMENT_NAMES = {
    '1': '내과', '2': '신경과', '3': '정신건강의학과', '4': '외과', '5': '정형외과',
    '6': '신경외과', '7': '흉부외과', '8': '성형외과', '9': '마취통증의학과', '10': '산부인과',
    '11': '소아청소년과', '12': '안과', '13': '이비인후과', '14': '피부과', '15': '비뇨의학과',
    '21': '재활의학과', '23': '가정의학과', '24': '응급의학과', '49': '치과', '80': '한의원',
}


# ──────────────────────────────────────────────────────────────────────────
#  API
# ──────────────────────────────────────────────────────────────────────────
@app.route('/api/primary_symptoms')
def get_primary_symptoms():
    return jsonify(primary_symptoms)


@app.route('/api/match_conditions')
def match_conditions():
    raw = request.args.get('symptoms', '')
    # 프론트엔드로부터 유저가 선택한 단계(1~5)를 받아옵니다. (기본값 3)
    stage = request.args.get('stage', default=3, type=int) 
    symptoms = [s.strip() for s in raw.split(',') if s.strip()]

    if not symptoms:
        return jsonify({'error': '증상을 1개 이상 선택해주세요.'}), 400

    unknown = [s for s in symptoms if s not in symptom_conditions]
    if unknown:
        return jsonify({'error': f'알 수 없는 증상이 포함되어 있습니다: {", ".join(unknown)}'}), 400

    sets = [set(symptom_conditions[s]) for s in symptoms]

    if len(sets) == 1:
        candidates = sets[0]
        match_type = 'single'
    else:
        inter = set.intersection(*sets)
        if inter:
            candidates = inter
            match_type = 'intersection'
        else:
            freq = {}
            for s in sets:
                for c in s:
                    freq[c] = freq.get(c, 0) + 1
            overlap = {c for c, n in freq.items() if n >= 2}
            if overlap:
                candidates = overlap
                match_type = 'partial_overlap'
            else:
                candidates = set.union(*sets)
                match_type = 'union'

    conditions = []
    for c in candidates:
        is_high_risk = c in HIGH_RISK_CONDITIONS
        
        # ──────────────────────────────────────────────────────────────────
        #위험도 단계(stage) 기반 가중치(Weight) 점수 부여
        # ──────────────────────────────────────────────────────────────────
        score = 0
        if is_high_risk:
            if stage >= 4:
                score += 100  # 위험도가 4~5일 때 고위험 질환을 최우선으로 노출
            else:
                score += 10   # 위험도가 낮아도 고위험 질환은 약간의 가중치 부여
        else:
            if stage <= 3:
                score += 50   # 위험도가 1~2일 때는 일반/경증 질환을 우선 노출
            else:
                score += 20   # 일반적인 상황

        conditions.append({
            'name': c,
            'department_codes': condition_departments.get(c, []),
            'department_names': [DEPARTMENT_NAMES.get(code, code) for code in condition_departments.get(c, [])],
            'high_risk': is_high_risk,
            'sort_score': score
        })

    conditions.sort(key=lambda x: (-x['sort_score'], x['name']))

    symptom_high_risk = any(s in HIGH_RISK_SYMPTOMS for s in symptoms)

    return jsonify({
        'conditions': conditions,
        'match_type': match_type,
        'multi_symptom': len(symptoms) > 1,
        'symptom_high_risk': symptom_high_risk,
    })


@app.route('/api/hospitals')
def get_hospitals():
    """
    department_codes  : 콤마로 구분된 진료과목코드 (예: 1,7,24)
    stage             : 유저 진단 단계 (4 또는 5)
    multi_symptom     : 'true' 이면 증상이 여러 개임 (추천 조건)
    high_risk_symptom : 'true' 이면 고위험군 증상이 체크됨 (바로가기 조건)
    """
    dept_param = request.args.get('department_codes') or request.args.get('department_code')
    lat = request.args.get('lat', type=float)
    lng = request.args.get('lng', type=float)
    radius = request.args.get('radius', default=5, type=float)
    
    stage = request.args.get('stage', type=int, default=0)
    multi_symptom = request.args.get('multi_symptom', default='false').lower() == 'true'
    high_risk_symptom = request.args.get('high_risk_symptom', default='false').lower() == 'true'

    if not dept_param or lat is None or lng is None:
        return jsonify({'error': 'department_codes, lat, lng 값이 필요합니다'}), 400

    codes = [c.strip() for c in dept_param.split(',') if c.strip()]
    is_strict_mode = high_risk_symptom or stage == 5
    
    is_recommend_mode = (multi_symptom or stage == 4) and not is_strict_mode

    query = Hospital.query.filter(Hospital.department_code.in_(codes))

    if is_strict_mode:
        query = query.filter(Hospital.facility_code.in_(HIGH_TIER_FACILITY_CODES))

    hospitals = query.all()

    def haversine(lon1, lat1, lon2, lat2):
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        c = 2 * asin(sqrt(a))
        return 6371 * c

    best = {}
    for h in hospitals:
        dist = haversine(lng, lat, h.longitude, h.latitude)
        if dist > radius:
            continue
        key = (h.name, round(h.latitude, 5), round(h.longitude, 5))
        if key not in best or dist < best[key]['distance_km']:
            d = h.to_dict()
            d['distance_km'] = round(dist, 2)
            
            if is_recommend_mode and h.facility_code in HIGH_TIER_FACILITY_CODES:
                d['is_recommended'] = True
            else:
                d['is_recommended'] = False
                
            best[key] = d

    nearby = sorted(best.values(), key=lambda x: x['distance_km'])
    return jsonify(nearby)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        load_csv_to_db('hospital_info2.csv')
    app.run(debug=True)
>>>>>>> Stashed changes
