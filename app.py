import streamlit as st
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

# 1. 페이지 테마 및 레이아웃 설정
st.set_page_config(page_title="AAD NEWS - Drone Portal", layout="wide", page_icon="🛸")

# CSS 커스텀 스타일링
st.markdown("""
    <style>
    .main { background-color: #f5f6f7; }
    .news-card { background-color: white; padding: 20px; border-radius: 4px; border: 1px solid #e3e7eb; margin-bottom: 12px; }
    .news-title { font-size: 18px; font-weight: bold; color: #222; text-decoration: none; }
    .news-title:hover { text-decoration: underline; color: #03c75a; }
    .news-meta { font-size: 12px; color: #888; margin-bottom: 8px; }
    .news-snippet { font-size: 14px; color: #444; line-height: 1.6; }
    .category-badge { background-color: #f1f3f5; color: #666; padding: 3px 8px; border-radius: 3px; font-size: 11px; font-weight: bold; margin-right: 6px; }
    
    /* 로고 이미지와 텍스트를 정렬하는 스타일 */
    .logo-container {
        display: flex;
        align-items: center;
        gap: 15px;
    }
    .logo-text-large {
        font-size: 28px;
        font-weight: bold;
        color: #03c75a;
        margin-bottom: -5px;
    }
    .logo-text-small {
        font-size: 12px;
        color: #888;
        letter-spacing: 0.5px;
    }
    </style>
    """, unsafe_allow_html=True)

# ⚠️ [필수] 본인의 네이버 API 키를 입력하세요!
# (여기에 발급받으신 본인의 Client ID와 Secret Key를 문자열로 꼭 채워주세요)
# 예: NAVER_CLIENT_ID = "abcde12345"
NAVER_CLIENT_ID = "Dp2Lci9FjuMH500UIKQ2".strip()
NAVER_CLIENT_SECRET = "RxFmGfyBA8".strip()

# 2. 헤더에 AAD NEWS 로고 배치
st.markdown(f"""
    <div class="logo-container">
        <img src="https://img.icons8.com/color/96/000000/drone.png" width="65">
        <div>
            <div class="logo-text-large">AAD NEWS</div>
            <div class="logo-text-small">AI ARMY DRONE NEWS</div>
        </div>
        <div style="font-size: 22px; font-weight: bold; color: #222; margin-left: 20px; border-left: 2px solid #e3e7eb; padding-left: 20px;">
            🛸Ai Army Drone News \n드론·국방·AI 종합 포털
        </div>
    </div>
""", unsafe_allow_html=True)

st.caption("드론과 융합된 군사 및 AI 이슈만 엄선하여, 최근 한 달 이내의 기사를 최신순으로 정렬합니다.")
st.markdown("<hr style='border: 1px solid #03c75a;'>", unsafe_allow_html=True)

# 3. 기사 실시간 텍스트 본문 추출 함수
def fetch_full_text(url):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    try:
        response = requests.get(url, headers=headers, timeout=3)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        content_div = soup.find(id="newsct_article") or soup.find(id="articleBodyContents") or soup.find(class_="article_body")
        if content_div:
            return content_div.get_text(separator="\n").strip()[:800] + "..."
        else:
            paragraphs = soup.find_all('p')
            return "\n\n".join([p.text.strip() for p in paragraphs if len(p.text.strip()) > 30])[:800] + "..."
    except:
        return "본문 상세 내용은 아래 원문 읽기 버튼을 이용해 주세요."

# 4. 네이버 뉴스 썸네일 이미지 추출 함수
def get_naver_thumbnail(url):
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    fallback_img = "https://via.placeholder.com/140x90.png?text=No+Image"
    try:
        response = requests.get(url, headers=headers, timeout=2)
        soup = BeautifulSoup(response.text, 'html.parser')
        img_tag = soup.find("meta", property="og:image")
        if img_tag and img_tag.get("content"):
            img_url = img_tag["content"].strip()
            if img_url.startswith("http://") or img_url.startswith("https://"):
                return img_url
    except:
        pass
    return fallback_img

# 5. 한 달 이내 필터링 및 드론 연관성 검증 API 호출 함수
@st.cache_data(ttl=300)
def fetch_portal_news(search_keyword):
    if NAVER_CLIENT_ID == "여기에_발급받은_Client_ID_입력" or not NAVER_CLIENT_ID:
        st.error("⚠️ 코드에 네이버 API 키를 먼저 입력해 주세요!")
        return []
        
    url = f"https://openapi.naver.com/v1/search/news.json?query={search_keyword}&display=100&sort=date"
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET
    }
    
    try:
        response = requests.get(url, headers=headers)
        data = response.json()
        
        news_db = []
        now = datetime.now()
        one_month_ago = now - timedelta(days=30)
        
        drone_must_keywords = ["드론", "drone", "무인기", "무인 체계", "UAM", "항공", "플라잉카", "무인기체", "쿼드콥터"]

        for item in data.get("items", []):
            pub_date_str = item["pubDate"]
            try:
                parsed_date = datetime.strptime(pub_date_str[:-6], "%a, %d %b %Y %H:%M:%S")
                if parsed_date < one_month_ago:
                    continue
                date_part = parsed_date.strftime("%Y-%m-%d %H:%M")
                sort_key = parsed_date  
            except:
                date_part = "최근 한 달 이내"
                sort_key = one_month_ago

            title = item["title"].replace("<b>", "").replace("</b>", "").replace("&quot;", '"').replace("&amp;", "&")
            description = item["description"].replace("<b>", "").replace("</b>", "").replace("&quot;", '"').replace("&amp;", "&")
            link = item["originallink"] if item["originallink"] else item["link"]
            
            text_to_check = (title + description).lower()
            if not any(keyword in text_to_check for keyword in drone_must_keywords):
                continue

            if any(banned in title for banned in ["드론 패턴", "완구용"]):
                continue

            if any(k in title for k in ["정부", "규제", "법안", "국토부", "정책"]):
                category, analysis = "📜 규제/정책", "정부 주도 규제 완화 및 제도적 가이드라인 동향입니다."
            elif any(k in title for k in ["전쟁", "안보", "군사", "공격", "방산", "러시아", "우크라", "전투", "군", "합참"]):
                category, analysis = "⚔️ 군사/안보", "국방 무인체계 및 군사 안보와 결합된 무인기 흐름입니다."
            elif any(k in title for k in ["배송", "UAM", "택시", "배달", "투자", "상용화", "물류", "기업"]):
                category, analysis = "🚀 비즈니스", "도심항공교통 실증 및 물류 비즈니스 트렌드입니다."
            else:
                category, analysis = "🔋 기술/트렌드", "AI 자율비행 알고리즘, 인공지능 센서 융합 등 테크 혁신입니다."
                
            news_db.append({
                "category": category,
                "title": title,
                "link": link,
                "snippet": description,
                "analysis": analysis,
                "date": date_part,
                "sort_key": sort_key  
            })
            
        news_db.sort(key=lambda x: x["sort_key"], reverse=True)
        return news_db
    except:
        return []

# 6. 사이드바 구성
st.sidebar.header("🔍 역대 뉴스 통합 검색")
user_search = st.sidebar.text_input("검색하고 싶은 키워드를 입력하세요", placeholder="예: 소형 드론, 우크라이나, 인공지능")

if user_search.strip():
    final_query = f"{user_search.strip()}"
    st.sidebar.info(f"💡 '{final_query}' 키워드로 최근 기사를 탐색합니다.")
else:
    final_query = "드론,군사,AI"

# 🔥 [업데이트] use_container_width=True 대신 width='stretch' 사용
if st.sidebar.button("🔄 포털 뉴스 동기화 (F5)", width='stretch'):
    st.cache_data.clear()
    st.toast("실시간 포털 테크 뉴스를 완벽하게 새로고침했습니다!")

st.sidebar.markdown("---")
selected_categories = st.sidebar.multiselect(
    "섹션별 뉴스 골라보기",
    ["🔋 기술/트렌드", "📜 규제/정책", "🚀 비즈니스", "⚔️ 군사/안보"],
    default=["🔋 기술/트렌드", "📜 규제/정책", "🚀 비즈니스", "⚔️ 군사/안보"]
)

# 7. 메인 화면 출력 로직
all_news = fetch_portal_news(final_query)
filtered_news = [n for n in all_news if n['category'] in selected_categories]

if not selected_categories:
    st.warning("⚠️ 왼쪽 섹션 메뉴에서 카테고리를 1개 이상 선택해야 뉴스가 노출됩니다.")
elif not all_news:
    st.info("💡 선택하신 검색 조건에 해당하는 최근 한 달 이내의 '드론 연관' 기사가 없습니다. 검색어를 바꾸거나 새로고침을 해주세요.")
else:
    st.success(f"🔥 드론 연관 검증을 통과한 핵심 뉴스 {len(filtered_news)}건이 최신순 타임라인으로 정렬되었습니다.")
    st.markdown("<br>", unsafe_allow_html=True)
    
    for idx, news in enumerate(filtered_news):
        st.markdown(f'<div class="news-card">', unsafe_allow_html=True)
        col1, col2 = st.columns([1, 5])
        
        with col1:
            thumb_img = get_naver_thumbnail(news['link'])
            try:
                # 🔥 [업데이트] use_container_width=True 대신 width='stretch' 사용
                st.image(thumb_img, width='stretch')
            except:
                st.image("https://via.placeholder.com/140x90.png?text=No+Image", width='stretch')
            
        with col2:
            st.markdown(f"""
                <span class="category-badge">{news['category']}</span>
                <span class="news-meta">📅 발행 시간: {news['date']} | 테크 포털 뉴스 센터</span><br>
                <a href="{news['link']}" target="_blank" class="news-title">{news['title']}</a>
                <p class="news-snippet" style="margin-top: 8px;">{news['snippet']}</p>
            """, unsafe_allow_html=True)
            
            with st.expander("📝 기사 전문 및 AI 모빌리티 분석 브리핑 보기"):
                st.write("**🤖 AI 관점 요약:**")
                st.info(news['analysis'])
                st.markdown("---")
                st.write("**📰 언론사 기사 본문:**")
                with st.spinner("기사 본문을 실시간 텍스트로 전환 중..."):
                    full_text = fetch_full_text(news['link'])
                st.write(full_text)
                st.markdown(f"[🔗 언론사 창에서 직접 읽기]({news['link']})")
                
        st.markdown('</div>', unsafe_allow_html=True)
