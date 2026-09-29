from flask import Flask, jsonify, request, send_file
from io import BytesIO
from pathlib import Path
import os
import sqlite3

app = Flask(__name__)
app.json.ensure_ascii = False
app.config['MAX_CONTENT_LENGTH'] = 64 * 1024

# 캡스톤 프로젝트 소개 기본 정보
PROJECT = {
    "title": "프로젝트 B.U - 건설 현장 관리 앱·웹",
    "summary": (
        "건설 현장의 복잡하고 분산된 보고 체계를 모바일 앱과 웹 대시보드로 통합하여 "
        "현장과 본사가 공정 진행 상황을 한곳에서 간편하게 확인하고 관리할 수 있도록 하는 서비스입니다. "
        "현장 관리자는 매일 사진, 텍스트, 공정별 진행도를 기록하고, 본사 관리자는 여러 현장의 보고 내용을 "
        "확인하여 승인 또는 반려할 수 있습니다. 이를 통해 보고 누락과 정보 분산을 줄이고, "
        "현장 진행 상황을 체계적으로 저장·관리하는 것을 목표로 합니다."
    ),
    "features": (
        "• 현장 보고: 현장 관리자가 모바일 앱에서 사진, 텍스트, 공정별 진행도를 입력하여 일일 보고를 작성합니다.\n"
        "• 통합 대시보드: 본사 관리자가 웹에서 여러 현장의 진행률과 보고 현황을 한눈에 확인합니다.\n"
        "• 승인·반려 관리: 제출된 보고 내용을 검토하고 승인 또는 반려하여 보고 절차를 체계화합니다.\n"
        "• 기록 관리: 현장별 보고 내용과 이미지를 저장하여 이전 작업 내역과 공정 진행 기록을 지속적으로 관리합니다."
    ),
    "technology": (
        "React와 React Native를 사용해 웹 대시보드와 모바일 앱 화면을 구성하고, "
        "Spring Boot 기반 REST API로 사용자·현장·공정·보고 데이터를 처리합니다. "
        "Spring Security와 JWT를 활용해 로그인과 역할별 접근 권한을 관리하며, "
        "MySQL을 이용해 현장 정보와 보고 데이터를 체계적으로 저장합니다."
    ),
    "team": (
        "프로젝트 B.U - 건설 현장 관리 앱·웹 개발팀\n"
        "• 프론트엔드(모바일): 현장 관리자용 로그인, 사진 촬영·업로드, 일일 보고 작성 화면 구현\n"
        "• 프론트엔드(웹): 본사 관리자용 현장 목록, 진행률 대시보드, 승인·반려 및 코멘트 화면 구현\n"
        "• DB·보안: 사용자·현장·공정·보고 데이터베이스 설계 및 운영, JWT 인증·인가와 권한 관리 구성\n"
        "• 서버·백엔드: 모바일·웹에서 사용하는 REST API 구현, 보고 데이터 처리 및 서비스 연동 담당"
    ),
}


@app.get('/api/health')
def health():
    # TODO: student_id와 name을 본인의 학번과 이름으로 변경하세요.
    return jsonify(status='ok', student_id='본인 학번', name='본인 이름')


@app.errorhandler(413)
def too_large(error):
    return jsonify(error='입력 내용이 너무 큽니다.'), 413


# 프로젝트 소개 내용을 프론트엔드에서 불러올 수 있도록 제공
@app.get('/api/project')
def project():
    return jsonify(PROJECT)


DATA_DIR = Path(os.environ.get('DATA_DIR', '/data'))
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB = DATA_DIR / 'views.db'

with sqlite3.connect(DB) as db:
    db.execute(
        'CREATE TABLE IF NOT EXISTS page_views '
        '(id INTEGER PRIMARY KEY CHECK(id=1), count INTEGER NOT NULL)'
    )
    db.execute('INSERT OR IGNORE INTO page_views VALUES (1, 0)')


@app.route('/api/views', methods=['GET', 'POST'])
def views():
    # UPDATE를 DB에서 수행하여 동시 요청으로 증가분이 사라지는 것을 막습니다.
    with sqlite3.connect(DB, timeout=10) as db:
        if request.method == 'POST':
            db.execute('UPDATE page_views SET count=count+1 WHERE id=1')
        count = db.execute('SELECT count FROM page_views WHERE id=1').fetchone()[0]
    return jsonify(views=count)


@app.post('/api/download')
def download():
    data = request.get_json(silent=True)

    # 기존 다운로드 기능 유지
    fields = ['title', 'summary', 'features', 'technology']
    if not isinstance(data, dict) or any(
        not isinstance(data.get(k), str) or not data[k].strip()
        for k in fields
    ):
        return jsonify(
            error='프로젝트명·소개·주요 기능·사용 기술을 모두 작성하세요.'
        ), 400

    # 팀 소개는 프론트엔드에서 보내면 해당 값을 사용하고,
    # 보내지 않으면 기본 팀 소개를 사용
    team = data.get('team', PROJECT['team'])
    if not isinstance(team, str) or not team.strip():
        team = PROJECT['team']

    values = [data[k] for k in fields] + [team]
    if any(len(value) > 5000 for value in values):
        return jsonify(error='각 항목은 5,000자 이내로 작성하세요.'), 400

    text = (
        f"# {data['title'].strip()}\n\n"
        f"## 프로젝트 소개\n{data['summary'].strip()}\n\n"
        f"## 주요 기능\n{data['features'].strip()}\n\n"
        f"## 사용 기술\n{data['technology'].strip()}\n\n"
        f"## 팀 소개\n{team.strip()}\n"
    )

    return send_file(
        BytesIO(text.encode('utf-8')),
        as_attachment=True,
        download_name='project-intro.md',
        mimetype='text/markdown; charset=utf-8'
    )


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
