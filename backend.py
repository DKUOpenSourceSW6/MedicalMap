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