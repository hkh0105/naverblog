"""썸네일 제작 페이지 - fabric.js 캔버스 DnD 에디터."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from naverblog.config import inject_secrets

inject_secrets()

st.set_page_config(
    page_title="썸네일 제작 | 보보쌤",
    page_icon="🖼️",
    layout="wide",
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; }
    .block-container { max-width: 1200px; padding-top: 1rem; padding-bottom: 0; }
    .page-header {
        background: linear-gradient(135deg, #0f766e 0%, #c85a3a 58%, #f2a65a 100%);
        padding: 1.5rem 2rem;
        border-radius: 1rem;
        color: white;
        margin-bottom: 1rem;
    }
    .page-header h1 { color: white !important; font-size: 1.3rem; font-weight: 700; margin: 0 0 0.2rem 0; }
    .page-header p { color: rgba(255,255,255,0.85); font-size: 0.82rem; margin: 0; font-weight: 300; }
    iframe { border: none !important; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="page-header">
    <h1>🖼️ 썸네일 제작</h1>
    <p>미리캔버스처럼 드래그 & 드롭으로 자유롭게 — 클릭해서 편집, 끌어서 이동</p>
</div>
""", unsafe_allow_html=True)

# ─── 글 생성에서 넘어온 경우 자동 채우기 ───
prefill_category = ""
prefill_title = "제목을 입력하세요"
prefill_subtitle = ""
last_gen = st.session_state.get("last_generation")
if last_gen:
    prefill_title = last_gen.get("topic", "") or "제목을 입력하세요"
    prefill_category = last_gen.get("category", "")

config_json = json.dumps({
    "category": prefill_category,
    "title": prefill_title,
    "subtitle": prefill_subtitle,
    "branding": "의대 간 보보쌤의 공부 & 입시 연구소",
}, ensure_ascii=False)

CANVAS_HTML = r"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<script src="https://cdnjs.cloudflare.com/ajax/libs/fabric.js/5.3.1/fabric.min.js"></script>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;600;700;900&family=Black+Han+Sans&family=Jua&family=Do+Hyeon&display=swap" rel="stylesheet">
<style>
@font-face {
    font-family: 'Cafe24Dangdanghae';
    src: url('https://cdn.jsdelivr.net/gh/projectnoonnu/noonfonts_2001@1.2/Cafe24Dangdanghae.woff') format('woff');
    font-weight: normal;
    font-display: swap;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: 'Noto Sans KR', sans-serif; background: #f8f9fa; overflow-x: hidden; }

/* ── 템플릿 바 ── */
#template-bar {
    display: flex; gap: 6px; padding: 10px 12px;
    background: white; border-radius: 10px;
    margin-bottom: 6px; flex-wrap: wrap;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    align-items: center;
}
#template-bar .bar-label {
    font-size: 11px; font-weight: 700; color: #0f766e;
    margin-right: 4px; white-space: nowrap;
}
.tmpl-btn {
    padding: 5px 12px; border-radius: 20px;
    border: 2px solid #e5e7eb; background: white;
    font-size: 11px; cursor: pointer; transition: all 0.15s;
    font-family: 'Noto Sans KR', sans-serif; font-weight: 500;
}
.tmpl-btn:hover { border-color: #f59e0b; }
.tmpl-btn.active { border-color: #f59e0b; background: #fffbeb; color: #b45309; }

/* ── 프리셋 바 ── */
#preset-bar {
    display: flex; gap: 6px; padding: 10px 12px;
    background: white; border-radius: 10px;
    margin-bottom: 6px; flex-wrap: wrap;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    align-items: center;
}
#preset-bar .bar-label {
    font-size: 11px; font-weight: 700; color: #6b7280;
    margin-right: 4px; white-space: nowrap;
}
.preset-btn {
    padding: 5px 12px; border-radius: 20px;
    border: 2px solid #e5e7eb; background: white;
    font-size: 11px; cursor: pointer; transition: all 0.15s;
    font-family: 'Noto Sans KR', sans-serif; font-weight: 500;
}
.preset-btn:hover { border-color: #5eead4; }
.preset-btn.active { border-color: #0f766e; background: #ecfdf5; color: #0f766e; }

/* ── 툴바 ── */
.toolbar-row {
    display: flex; align-items: center; gap: 8px; padding: 7px 12px;
    background: white; border-radius: 10px;
    margin-bottom: 6px; flex-wrap: wrap;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    min-height: 40px;
}
.toolbar-row label {
    display: flex; align-items: center; gap: 3px;
    font-size: 11px; color: #555; white-space: nowrap;
}
.toolbar-row select, .toolbar-row input[type="number"] {
    padding: 3px 5px; border: 1px solid #ddd; border-radius: 6px;
    font-size: 11px; font-family: 'Noto Sans KR'; background: white;
}
.toolbar-row input[type="color"] {
    width: 26px; height: 26px; border: 1px solid #ddd;
    border-radius: 6px; cursor: pointer; padding: 1px;
}
.toolbar-row input[type="range"] { width: 70px; }
.tb-sep { width: 1px; height: 22px; background: #e5e7eb; flex-shrink: 0; }
.tb-btn {
    padding: 4px 10px; border-radius: 6px; border: 1px solid #ddd;
    background: white; font-size: 11px; cursor: pointer;
    font-family: 'Noto Sans KR'; transition: all 0.15s; white-space: nowrap;
}
.tb-btn:hover { background: #f3f4f6; }
.tb-btn.primary { background: #0f766e; color: white; border-color: #0f766e; }
.tb-btn.primary:hover { background: #115e59; }
.tb-btn.danger { color: #ef4444; border-color: #fca5a5; }
.tb-btn.danger:hover { background: #fef2f2; }
.tb-btn.active { background: #ecfdf5; border-color: #5eead4; color: #0f766e; }
.tb-btn[disabled] { opacity: 0.4; pointer-events: none; }
#selected-info { font-size: 11px; color: #888; font-weight: 500; min-width: 60px; }
#obj-controls { display: none; align-items: center; gap: 6px; flex-wrap: wrap; }

/* ── 캔버스 ── */
#canvas-wrapper {
    background: white; border-radius: 10px; padding: 12px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    display: flex; justify-content: center; align-items: center;
    overflow: hidden; position: relative;
}
#canvas-wrapper .canvas-container { border-radius: 4px; }

/* ── 스냅 가이드라인 ── */
.guide-line {
    position: absolute; background: #0f766e; z-index: 999; pointer-events: none; opacity: 0.6;
}
.guide-line.horizontal { height: 1px; left: 0; right: 0; }
.guide-line.vertical { width: 1px; top: 0; bottom: 0; }

.help-text { font-size: 11px; color: #999; text-align: center; margin-top: 6px; }

/* ── 숨겨진 파일 input ── */
#imgUploadInput, #bgImgInput { display: none; }
</style>
</head>
<body>

<!-- 템플릿 바 -->
<div id="template-bar"></div>

<!-- 프리셋 바 -->
<div id="preset-bar"></div>

<!-- 상단 툴바: 캔버스 설정 + 요소 추가 -->
<div class="toolbar-row">
    <label>🖼️
        <select id="canvasSize">
            <option value="1080x1080" selected>1080×1080 정사각</option>
            <option value="1200x628">1200×628 블로그</option>
            <option value="1920x1080">1920×1080 유튜브</option>
            <option value="1080x1920">1080×1920 스토리</option>
            <option value="800x400">800×400 배너</option>
        </select>
    </label>
    <label>배경<input type="color" id="bgColor" value="#F5C6AA"></label>
    <button class="tb-btn" id="bgImgBtn" title="배경 이미지">🏞️ 배경이미지</button>
    <button class="tb-btn" id="bgImgClearBtn" title="배경 이미지 제거" style="display:none;">✕ 배경제거</button>
    <input type="file" id="bgImgInput" accept="image/*">
    <div class="tb-sep"></div>
    <button class="tb-btn" id="addTextBtn">＋ 텍스트</button>
    <button class="tb-btn" id="addRectBtn">＋ 사각형</button>
    <button class="tb-btn" id="addCircleBtn">＋ 원형</button>
    <button class="tb-btn" id="addLineBtn">＋ 구분선</button>
    <button class="tb-btn" id="addBrushLineBtn">＋ 브러시 선</button>
    <button class="tb-btn" id="addTapeBtn">＋ 덕테이프</button>
    <button class="tb-btn" id="imgUploadBtn">＋ 이미지</button>
    <input type="file" id="imgUploadInput" accept="image/*">
    <div style="flex:1"></div>
    <button class="tb-btn" id="gridToggleBtn" title="그리드 토글">📐 그리드</button>
    <button class="tb-btn primary" id="downloadBtn">📥 다운로드</button>
</div>

<!-- 선택 요소 속성 툴바 -->
<div class="toolbar-row" id="propBar" style="display:none;">
    <span id="selected-info">요소 선택됨</span>
    <div class="tb-sep"></div>

    <!-- 텍스트 전용 속성 -->
    <div id="textProps" style="display:none; align-items:center; gap:6px; flex-wrap:wrap;">
        <label>🎨<input type="color" id="textColor" value="#1a1a1a"></label>
        <label>글꼴
            <select id="fontSelect">
                <option value="Cafe24Dangdanghae" selected>당당해</option>
                <option value="Noto Sans KR">Noto Sans KR</option>
                <option value="Black Han Sans">Black Han Sans</option>
                <option value="Jua">Jua</option>
                <option value="Do Hyeon">Do Hyeon</option>
            </select>
        </label>
        <label>크기 <input type="range" id="fontSize" min="12" max="200" value="80"> <span id="fontSizeLabel">80</span></label>
        <label>굵기
            <select id="fontWeight">
                <option value="400">보통</option>
                <option value="700" selected>굵게</option>
                <option value="900">아주 굵게</option>
            </select>
        </label>
        <div class="tb-sep"></div>
        <button class="tb-btn" id="alignLeft" title="왼쪽 정렬">⬅</button>
        <button class="tb-btn active" id="alignCenter" title="가운데 정렬">⬛</button>
        <button class="tb-btn" id="alignRight" title="오른쪽 정렬">➡</button>
        <div class="tb-sep"></div>
        <label>✨ 형광펜<input type="checkbox" id="hlToggle"></label>
        <label>🖍️<input type="color" id="hlColor" value="#E8967D"></label>
        <label>두께 <input type="range" id="hlThickness" min="10" max="100" value="40"> <span id="hlThicknessLabel">40</span>%</label>
        <div class="tb-sep"></div>
        <label>그림자<input type="checkbox" id="shadowToggle"></label>
        <label>외곽선<input type="checkbox" id="strokeToggle"></label>
        <label><input type="color" id="strokeColor" value="#ffffff"></label>
        <label><input type="range" id="strokeWidth" min="1" max="10" value="2" style="width:50px;"> <span id="strokeWidthLabel">2</span></label>
    </div>

    <!-- 도형 전용 속성 -->
    <div id="shapeProps" style="display:none; align-items:center; gap:6px; flex-wrap:wrap;">
        <label>채우기<input type="color" id="shapeFill" value="#E8967D"></label>
        <label>테두리<input type="color" id="shapeStroke" value="#E8967D"></label>
        <label>두께 <input type="range" id="shapeStrokeW" min="0" max="20" value="0"> <span id="shapeStrokeWLabel">0</span></label>
        <label>둥글기 <input type="range" id="shapeRadius" min="0" max="50" value="0"> <span id="shapeRadiusLabel">0</span></label>
    </div>

    <!-- 공통 속성 -->
    <div class="tb-sep"></div>
    <label>투명도 <input type="range" id="opacityRange" min="0" max="100" value="100"> <span id="opacityLabel">100</span>%</label>
    <div class="tb-sep"></div>
    <button class="tb-btn" id="bringFrontBtn" title="맨 앞으로">⬆ 앞</button>
    <button class="tb-btn" id="bringUpBtn" title="하나 앞으로">↑</button>
    <button class="tb-btn" id="sendDownBtn" title="하나 뒤로">↓</button>
    <button class="tb-btn" id="sendBackBtn" title="맨 뒤로">⬇ 뒤</button>
    <div class="tb-sep"></div>
    <button class="tb-btn" id="duplicateBtn" title="복제">📋 복제</button>
    <button class="tb-btn" id="lockBtn" title="잠금/해제">🔒</button>
    <button class="tb-btn danger" id="deleteBtn">🗑️ 삭제</button>
</div>

<!-- 캔버스 -->
<div id="canvas-wrapper">
    <canvas id="c"></canvas>
</div>

<div class="help-text">
    더블클릭 = 텍스트 편집 · 드래그 = 이동 · 모서리 드래그 = 크기 조절 · Delete = 삭제 · Ctrl+D = 복제 · Ctrl+Z = 되돌리기 · Ctrl+Shift+Z = 다시실행
</div>

<script>
// ═══════════════════════════════════════
// 설정
// ═══════════════════════════════════════
var CONFIG = __CONFIG_JSON__;

var PRESETS = {
    "보보쌤 살구": { bg:"#F5C6AA", text:"#1a1a1a", hl:"#E8967D", accent:"#C85A3A", brand:"#8B5E3C", sub:"#C85A3A" },
    "보보쌤 크림": { bg:"#FDF6EC", text:"#1a1a1a", hl:"#FFE066", accent:"#C85A3A", brand:"#8B5E3C", sub:"#C85A3A" },
    "퍼플":       { bg:"#F5F0FF", text:"#1a1a1a", hl:"#C4B5FD", accent:"#7c3aed", brand:"#7c3aed", sub:"#7c3aed" },
    "화이트":     { bg:"#FFFFFF", text:"#1a1a1a", hl:"#FFE066", accent:"#3B82F6", brand:"#999999", sub:"#3B82F6" },
    "핑크":       { bg:"#FFF0F5", text:"#1a1a1a", hl:"#FBCFE8", accent:"#EC4899", brand:"#EC4899", sub:"#EC4899" },
    "네이비":     { bg:"#1E293B", text:"#FFFFFF", hl:"#3B82F6", accent:"#60A5FA", brand:"#94A3B8", sub:"#60A5FA" },
    "다크":       { bg:"#18181B", text:"#FFFFFF", hl:"#A78BFA", accent:"#A78BFA", brand:"#71717A", sub:"#A78BFA" },
    "민트":       { bg:"#F0FDF4", text:"#1a1a1a", hl:"#86EFAC", accent:"#059669", brand:"#059669", sub:"#059669" }
};

var currentPreset = "보보쌤 살구";
var currentTemplate = "bobo_default";

// ═══════════════════════════════════════
// 템플릿 정의
// ═══════════════════════════════════════
var TEMPLATES = {
    "bobo_default": {
        name: "보보쌤 기본",
        desc: "제목 + 브러시선 + 부제목 + 푸터",
        build: function(p) {
            var titleText = CONFIG.title || '제목을 입력하세요';
            var titleLines = titleText.split('\n').filter(function(l) { return l.trim(); });
            if (titleLines.length === 0) titleLines = ['제목을 입력하세요'];

            var startY = CH * 0.22;
            var curY = startY;

            if (CONFIG.category) {
                createText(CONFIG.category, {
                    left: CW / 2, top: curY,
                    fontSize: 28, fontWeight: '500',
                    fontFamily: 'Noto Sans KR',
                    fill: p.accent, etype: 'category',
                });
                curY += 50;
            }

            for (var i = 0; i < titleLines.length; i++) {
                createText(titleLines[i], {
                    left: CW / 2, top: curY,
                    fontFamily: 'Cafe24Dangdanghae',
                    fontSize: 90, fontWeight: '400',
                    fill: p.text, etype: 'title',
                });
                curY += 120;
            }

            curY += 20;
            addBrushLine({ y: curY, color: p.hl, strokeWidth: 8 });
            curY += 50;

            if (CONFIG.subtitle) {
                createText(CONFIG.subtitle, {
                    left: CW / 2, top: curY,
                    fontFamily: 'Cafe24Dangdanghae',
                    fontSize: 40, fontWeight: '400',
                    fill: p.sub || p.accent, etype: 'subtitle',
                });
            }

            createText(CONFIG.branding, {
                left: CW - 60, top: CH - 70,
                fontFamily: 'Noto Sans KR',
                fontSize: 24, fontWeight: '400',
                fill: p.brand, etype: 'branding',
                textAlign: 'right', originX: 'right',
            });
        }
    },
    "simple_center": {
        name: "심플 센터",
        desc: "큰 제목 하나 가운데",
        build: function(p) {
            var titleText = CONFIG.title || '제목을 입력하세요';
            createText(titleText, {
                left: CW / 2, top: CH * 0.35,
                fontFamily: 'Cafe24Dangdanghae',
                fontSize: 110, fontWeight: '400',
                fill: p.text, etype: 'title',
            });

            // 하단 얇은 직선 구분선
            var line = new fabric.Line([CW * 0.3, CH * 0.62, CW * 0.7, CH * 0.62], {
                stroke: p.hl, strokeWidth: 4,
                selectable: true, _etype: 'separator',
            });
            canvas.add(line);

            createText(CONFIG.branding, {
                left: CW / 2, top: CH * 0.72,
                fontFamily: 'Noto Sans KR',
                fontSize: 22, fontWeight: '400',
                fill: p.brand, etype: 'branding',
            });
        }
    },
    "category_focus": {
        name: "카테고리 강조",
        desc: "상단 카테고리 라벨 + 제목 + 부제목",
        build: function(p) {
            // 상단 둥근 라벨 배경
            var labelBg = new fabric.Rect({
                left: CW / 2 - 100, top: CH * 0.12,
                width: 200, height: 45,
                fill: p.accent, rx: 22, ry: 22,
                _etype: 'decoration',
            });
            canvas.add(labelBg);

            createText(CONFIG.category || '카테고리', {
                left: CW / 2, top: CH * 0.125,
                fontFamily: 'Noto Sans KR',
                fontSize: 22, fontWeight: '700',
                fill: '#FFFFFF', etype: 'category',
            });

            var titleText = CONFIG.title || '제목을 입력하세요';
            createText(titleText, {
                left: CW / 2, top: CH * 0.30,
                fontFamily: 'Cafe24Dangdanghae',
                fontSize: 85, fontWeight: '400',
                fill: p.text, etype: 'title',
            });

            addBrushLine({ y: CH * 0.56, color: p.hl, strokeWidth: 6 });

            if (CONFIG.subtitle) {
                createText(CONFIG.subtitle, {
                    left: CW / 2, top: CH * 0.64,
                    fontFamily: 'Noto Sans KR',
                    fontSize: 32, fontWeight: '500',
                    fill: p.sub || p.accent, etype: 'subtitle',
                });
            }

            createText(CONFIG.branding, {
                left: CW / 2, top: CH - 80,
                fontFamily: 'Noto Sans KR',
                fontSize: 20, fontWeight: '400',
                fill: p.brand, etype: 'branding',
            });
        }
    },
    "left_modern": {
        name: "좌정렬 모던",
        desc: "왼쪽 정렬 + 세로 포인트선",
        build: function(p) {
            // 좌측 세로 포인트 바
            var vbar = new fabric.Rect({
                left: 80, top: CH * 0.22,
                width: 8, height: CH * 0.45,
                fill: p.accent, rx: 4, ry: 4,
                _etype: 'decoration',
            });
            canvas.add(vbar);

            if (CONFIG.category) {
                createText(CONFIG.category, {
                    left: 120, top: CH * 0.23,
                    fontFamily: 'Noto Sans KR',
                    fontSize: 24, fontWeight: '600',
                    fill: p.accent, etype: 'category',
                    textAlign: 'left', originX: 'left',
                });
            }

            var titleText = CONFIG.title || '제목을 입력하세요';
            var tLines = titleText.split('\n').filter(function(l) { return l.trim(); });
            if (tLines.length === 0) tLines = ['제목을 입력하세요'];
            var curY = CH * 0.32;
            for (var i = 0; i < tLines.length; i++) {
                createText(tLines[i], {
                    left: 120, top: curY,
                    fontFamily: 'Cafe24Dangdanghae',
                    fontSize: 80, fontWeight: '400',
                    fill: p.text, etype: 'title',
                    textAlign: 'left', originX: 'left',
                });
                curY += 105;
            }

            if (CONFIG.subtitle) {
                createText(CONFIG.subtitle, {
                    left: 120, top: curY + 20,
                    fontFamily: 'Noto Sans KR',
                    fontSize: 28, fontWeight: '400',
                    fill: p.sub || p.accent, etype: 'subtitle',
                    textAlign: 'left', originX: 'left',
                });
            }

            createText(CONFIG.branding, {
                left: CW - 60, top: CH - 70,
                fontFamily: 'Noto Sans KR',
                fontSize: 22, fontWeight: '400',
                fill: p.brand, etype: 'branding',
                textAlign: 'right', originX: 'right',
            });
        }
    },
    "two_tone": {
        name: "투톤 분할",
        desc: "상단 색상 + 하단 텍스트",
        build: function(p) {
            // 상단 색상 영역 (캔버스 절반)
            var topBlock = new fabric.Rect({
                left: 0, top: 0,
                width: CW, height: CH * 0.45,
                fill: p.accent,
                selectable: true,
                _etype: 'decoration',
            });
            canvas.add(topBlock);

            // 상단 영역에 카테고리
            if (CONFIG.category) {
                createText(CONFIG.category, {
                    left: CW / 2, top: CH * 0.15,
                    fontFamily: 'Noto Sans KR',
                    fontSize: 26, fontWeight: '600',
                    fill: '#FFFFFF', etype: 'category',
                });
            }

            // 상단 영역에 큰 아이콘/숫자
            createText('📚', {
                left: CW / 2, top: CH * 0.25,
                fontFamily: 'Noto Sans KR',
                fontSize: 60, fontWeight: '400',
                fill: '#FFFFFF', etype: 'custom',
            });

            // 하단 영역에 제목
            var titleText = CONFIG.title || '제목을 입력하세요';
            createText(titleText, {
                left: CW / 2, top: CH * 0.55,
                fontFamily: 'Cafe24Dangdanghae',
                fontSize: 75, fontWeight: '400',
                fill: p.text, etype: 'title',
            });

            if (CONFIG.subtitle) {
                createText(CONFIG.subtitle, {
                    left: CW / 2, top: CH * 0.73,
                    fontFamily: 'Noto Sans KR',
                    fontSize: 28, fontWeight: '400',
                    fill: p.sub || p.accent, etype: 'subtitle',
                });
            }

            createText(CONFIG.branding, {
                left: CW / 2, top: CH - 70,
                fontFamily: 'Noto Sans KR',
                fontSize: 20, fontWeight: '400',
                fill: p.brand, etype: 'branding',
            });
        }
    },
    "point_box": {
        name: "포인트 박스",
        desc: "배경 박스 위 제목",
        build: function(p) {
            // 큰 포인트 박스 (가운데)
            var box = new fabric.Rect({
                left: CW * 0.08, top: CH * 0.1,
                width: CW * 0.84, height: CH * 0.8,
                fill: 'transparent',
                stroke: p.accent, strokeWidth: 6,
                rx: 30, ry: 30,
                _etype: 'decoration',
            });
            canvas.add(box);

            // 안쪽 작은 장식 원
            var circle1 = new fabric.Circle({
                left: CW * 0.15, top: CH * 0.15,
                radius: 30, fill: p.hl + '60',
                selectable: true, _etype: 'decoration',
            });
            canvas.add(circle1);
            var circle2 = new fabric.Circle({
                left: CW * 0.78, top: CH * 0.72,
                radius: 45, fill: p.hl + '40',
                selectable: true, _etype: 'decoration',
            });
            canvas.add(circle2);

            if (CONFIG.category) {
                createText(CONFIG.category, {
                    left: CW / 2, top: CH * 0.25,
                    fontFamily: 'Noto Sans KR',
                    fontSize: 24, fontWeight: '600',
                    fill: p.accent, etype: 'category',
                });
            }

            var titleText = CONFIG.title || '제목을 입력하세요';
            createText(titleText, {
                left: CW / 2, top: CH * 0.37,
                fontFamily: 'Cafe24Dangdanghae',
                fontSize: 85, fontWeight: '400',
                fill: p.text, etype: 'title',
            });

            addBrushLine({ y: CH * 0.58, color: p.hl, strokeWidth: 6 });

            if (CONFIG.subtitle) {
                createText(CONFIG.subtitle, {
                    left: CW / 2, top: CH * 0.65,
                    fontFamily: 'Noto Sans KR',
                    fontSize: 30, fontWeight: '500',
                    fill: p.sub || p.accent, etype: 'subtitle',
                });
            }

            createText(CONFIG.branding, {
                left: CW / 2, top: CH - 100,
                fontFamily: 'Noto Sans KR',
                fontSize: 20, fontWeight: '400',
                fill: p.brand, etype: 'branding',
            });
        }
    },
    "duct_tape_note": {
        name: "덕테이프 메모",
        desc: "찢긴 테이프 + 메모지 강조",
        build: function(p) {
            var paper = new fabric.Rect({
                left: CW * 0.12, top: CH * 0.15,
                width: CW * 0.76, height: CH * 0.62,
                fill: '#fffdf7',
                stroke: '#ead7b8',
                strokeWidth: 2,
                rx: 18, ry: 18,
                shadow: new fabric.Shadow({
                    color: 'rgba(80, 48, 24, 0.16)',
                    blur: 18,
                    offsetX: 0,
                    offsetY: 8,
                }),
                _etype: 'decoration',
            });
            canvas.add(paper);

            addDuctTape({
                left: CW * 0.32,
                top: CH * 0.14,
                width: CW * 0.28,
                height: 56,
                angle: -7,
                color: '#d9d3c1',
                opacity: 0.92,
            });
            addDuctTape({
                left: CW * 0.68,
                top: CH * 0.14,
                width: CW * 0.28,
                height: 56,
                angle: 7,
                color: '#e8d6b8',
                opacity: 0.92,
            });

            if (CONFIG.category) {
                createText(CONFIG.category, {
                    left: CW / 2, top: CH * 0.25,
                    fontFamily: 'Noto Sans KR',
                    fontSize: 24, fontWeight: '700',
                    fill: p.accent, etype: 'category',
                });
            }

            var titleText = CONFIG.title || '제목을 입력하세요';
            createText(titleText, {
                left: CW / 2, top: CH * 0.36,
                fontFamily: 'Cafe24Dangdanghae',
                fontSize: 82, fontWeight: '400',
                fill: p.text, etype: 'title',
            });

            if (CONFIG.subtitle) {
                createText(CONFIG.subtitle, {
                    left: CW / 2, top: CH * 0.59,
                    fontFamily: 'Noto Sans KR',
                    fontSize: 30, fontWeight: '500',
                    fill: p.sub || p.accent, etype: 'subtitle',
                });
            }

            addDuctTape({
                left: CW * 0.5,
                top: CH * 0.76,
                width: CW * 0.36,
                height: 44,
                angle: 1,
                color: '#f0dfbf',
                opacity: 0.75,
            });

            createText(CONFIG.branding, {
                left: CW / 2, top: CH * 0.79,
                fontFamily: 'Noto Sans KR',
                fontSize: 20, fontWeight: '500',
                fill: p.brand, etype: 'branding',
            });
        }
    }
};

// ═══════════════════════════════════════
// Undo / Redo 스택
// ═══════════════════════════════════════
var undoStack = [];
var redoStack = [];
var maxUndo = 30;
function saveState() {
    var json = canvas.toJSON(['_etype','_hlEnabled','_hlColor','_hlThickness','_isHL','_locked']);
    undoStack.push(JSON.stringify(json));
    if (undoStack.length > maxUndo) undoStack.shift();
    redoStack = [];
}
function undo() {
    if (undoStack.length < 2) return;
    var current = undoStack.pop();
    redoStack.push(current);
    var prev = undoStack[undoStack.length - 1];
    canvas.loadFromJSON(prev, function() {
        canvas.renderAll();
        rebindHLEvents();
    });
}
function redo() {
    if (redoStack.length === 0) return;
    var next = redoStack.pop();
    undoStack.push(next);
    canvas.loadFromJSON(next, function() {
        canvas.renderAll();
        rebindHLEvents();
    });
}

// ═══════════════════════════════════════
// 캔버스 초기화
// ═══════════════════════════════════════
var CW = 1080, CH = 1080;
var displayW = Math.min(document.documentElement.clientWidth - 50, 900);
var scale = displayW / CW;
var displayH = CH * scale;

var canvas = new fabric.Canvas('c', {
    width: displayW,
    height: displayH,
    backgroundColor: PRESETS[currentPreset].bg,
    preserveObjectStacking: true,
});
canvas.setZoom(scale);

// ═══════════════════════════════════════
// 그리드 / 스냅 가이드라인
// ═══════════════════════════════════════
var gridVisible = false;
var gridLines = [];
var snapThreshold = 15;
var guideLines = { h: null, v: null };

function drawGrid() {
    removeGrid();
    if (!gridVisible) return;
    var step = CW / 10;
    for (var x = step; x < CW; x += step) {
        var vl = new fabric.Line([x, 0, x, CH], {
            stroke: '#ddd', strokeWidth: 1, strokeDashArray: [5, 5],
            selectable: false, evented: false, _isGrid: true, opacity: 0.5,
        });
        canvas.add(vl);
        canvas.sendToBack(vl);
        gridLines.push(vl);
    }
    for (var y = step; y < CH; y += step) {
        var hl = new fabric.Line([0, y, CW, y], {
            stroke: '#ddd', strokeWidth: 1, strokeDashArray: [5, 5],
            selectable: false, evented: false, _isGrid: true, opacity: 0.5,
        });
        canvas.add(hl);
        canvas.sendToBack(hl);
        gridLines.push(hl);
    }
    // 중심선 강조
    var cx = new fabric.Line([CW/2, 0, CW/2, CH], {
        stroke: '#bbb', strokeWidth: 1, strokeDashArray: [8, 4],
        selectable: false, evented: false, _isGrid: true, opacity: 0.6,
    });
    var cy = new fabric.Line([0, CH/2, CW, CH/2], {
        stroke: '#bbb', strokeWidth: 1, strokeDashArray: [8, 4],
        selectable: false, evented: false, _isGrid: true, opacity: 0.6,
    });
    canvas.add(cx); canvas.add(cy);
    canvas.sendToBack(cx); canvas.sendToBack(cy);
    gridLines.push(cx, cy);
    canvas.renderAll();
}
function removeGrid() {
    gridLines.forEach(function(l) { canvas.remove(l); });
    gridLines = [];
    canvas.renderAll();
}

// 스냅 가이드: 오브젝트 이동 시 중심 스냅
canvas.on('object:moving', function(e) {
    var obj = e.target;
    if (!obj || obj._isGrid || obj._isHL) return;
    var centerX = obj.left + obj.getScaledWidth() / 2;
    var centerY = obj.top + obj.getScaledHeight() / 2;
    if (obj.originX === 'center') centerX = obj.left;
    if (obj.originY === 'center') centerY = obj.top;

    // 수평 중심 스냅
    if (Math.abs(centerX - CW / 2) < snapThreshold) {
        if (obj.originX === 'center') obj.set('left', CW / 2);
        else obj.set('left', CW / 2 - obj.getScaledWidth() / 2);
    }
    // 수직 중심 스냅
    if (Math.abs(centerY - CH / 2) < snapThreshold) {
        if (obj.originY === 'center') obj.set('top', CH / 2);
        else obj.set('top', CH / 2 - obj.getScaledHeight() / 2);
    }
});

document.getElementById('gridToggleBtn').onclick = function() {
    gridVisible = !gridVisible;
    this.classList.toggle('active', gridVisible);
    drawGrid();
};

// ═══════════════════════════════════════
// 템플릿 버튼 생성
// ═══════════════════════════════════════
var templateBar = document.getElementById('template-bar');
var tmplLabel = document.createElement('span');
tmplLabel.className = 'bar-label';
tmplLabel.textContent = '레이아웃';
templateBar.appendChild(tmplLabel);

Object.keys(TEMPLATES).forEach(function(key) {
    var tmpl = TEMPLATES[key];
    var btn = document.createElement('button');
    btn.className = 'tmpl-btn' + (key === currentTemplate ? ' active' : '');
    btn.textContent = tmpl.name;
    btn.title = tmpl.desc;
    btn.dataset.tmpl = key;
    btn.onclick = function() { applyTemplate(key); };
    templateBar.appendChild(btn);
});

function applyTemplate(key) {
    currentTemplate = key;
    var p = PRESETS[currentPreset];

    // 모든 오브젝트 제거
    canvas.getObjects().slice().forEach(function(obj) {
        canvas.remove(obj);
    });
    canvas.setBackgroundColor(p.bg, function() { canvas.renderAll(); });
    canvas.setBackgroundImage(null, function() { canvas.renderAll(); });
    document.getElementById('bgImgClearBtn').style.display = 'none';

    undoStack = [];
    redoStack = [];

    TEMPLATES[key].build(p);

    if (gridVisible) drawGrid();
    canvas.renderAll();
    saveState();

    document.querySelectorAll('.tmpl-btn').forEach(function(b) {
        b.classList.toggle('active', b.dataset.tmpl === key);
    });
}

// ═══════════════════════════════════════
// 프리셋 버튼 생성
// ═══════════════════════════════════════
var presetBar = document.getElementById('preset-bar');
var pLabel = document.createElement('span');
pLabel.className = 'bar-label';
pLabel.textContent = '색상';
presetBar.appendChild(pLabel);

Object.keys(PRESETS).forEach(function(name) {
    var btn = document.createElement('button');
    btn.className = 'preset-btn' + (name === currentPreset ? ' active' : '');
    btn.textContent = name;
    btn.dataset.preset = name;
    btn.onclick = function() { applyPreset(name); };
    presetBar.appendChild(btn);
});

function applyPreset(name) {
    currentPreset = name;
    var p = PRESETS[name];
    canvas.setBackgroundColor(p.bg, function() { canvas.renderAll(); });

    canvas.getObjects().forEach(function(obj) {
        if (obj._isHL || obj._isGrid) return;
        if (obj._etype === 'category') obj.set('fill', p.accent);
        else if (obj._etype === 'branding') obj.set('fill', p.brand);
        else if (obj._etype === 'subtitle') obj.set('fill', p.sub || p.accent);
        else if (obj._etype === 'separator' || obj._etype === 'brushline') obj.set('stroke', p.hl);
        else if (obj._etype === 'decoration') {
            if (obj.type === 'rect' && obj.stroke && obj.fill === 'transparent') obj.set('stroke', p.accent);
            else if (obj.type === 'rect' && obj.fill !== 'transparent') obj.set('fill', p.accent);
            else if (obj.type === 'circle') obj.set('fill', p.hl + '60');
        }
        else if (obj.type === 'i-text' || obj.type === 'text') obj.set('fill', p.text);
    });

    // 형광펜 색상 업데이트
    canvas.getObjects().forEach(function(obj) {
        if (obj._hlRect) {
            obj._hlColor = p.hl;
            obj._hlRect.set('fill', p.hl);
        }
    });
    canvas.renderAll();
    document.getElementById('bgColor').value = p.bg;

    document.querySelectorAll('.preset-btn').forEach(function(b) {
        b.classList.toggle('active', b.dataset.preset === name);
    });
    saveState();
}

// ═══════════════════════════════════════
// 텍스트 & 형광펜 헬퍼
// ═══════════════════════════════════════
function createText(text, opts) {
    var fontFamily = opts.fontFamily || 'Cafe24Dangdanghae';
    var itext = new fabric.IText(text, {
        left: opts.left || CW / 2,
        top: opts.top || CH / 2,
        fontFamily: fontFamily,
        fontSize: opts.fontSize || 80,
        fontWeight: String(opts.fontWeight || '700'),
        fill: opts.fill || '#1a1a1a',
        textAlign: opts.textAlign || 'center',
        originX: opts.originX || 'center',
        originY: opts.originY || 'top',
        lineHeight: 1.15,
        _etype: opts.etype || 'title',
        _hlEnabled: false,
        _hlColor: opts.hlColor || PRESETS[currentPreset].hl,
        _hlThickness: opts.hlThickness || 40,
    });

    canvas.add(itext);

    if (opts.hlEnabled) {
        addHL(itext, opts.hlColor || PRESETS[currentPreset].hl, opts.hlThickness || 40);
    }

    bindHLEvents(itext);
    return itext;
}

function bindHLEvents(itext) {
    itext.on('moving',   function() { syncHL(this); });
    itext.on('scaling',  function() { syncHL(this); });
    itext.on('modified', function() { syncHL(this); saveState(); });
    itext.on('changed',  function() { syncHL(this); });
    itext.on('editing:exited', function() { syncHL(this); saveState(); });
}

function rebindHLEvents() {
    canvas.getObjects().forEach(function(obj) {
        if (obj.type === 'i-text') {
            obj.off('moving'); obj.off('scaling'); obj.off('modified'); obj.off('changed'); obj.off('editing:exited');
            bindHLEvents(obj);
        }
    });
}

function getTextBounds(obj) {
    var w = obj.getScaledWidth();
    var h = obj.getScaledHeight();
    var left = obj.left;
    var top = obj.top;
    if (obj.originX === 'center') left -= w / 2;
    if (obj.originY === 'center') top -= h / 2;
    return { left: left, top: top, width: w, height: h };
}

function addHL(textObj, color, thickness) {
    removeHL(textObj);
    thickness = thickness || textObj._hlThickness || 40;
    var b = getTextBounds(textObj);
    var hlRatio = thickness / 100;
    var rect = new fabric.Rect({
        left: b.left - 8,
        top: b.top + b.height * (1 - hlRatio),
        width: b.width + 16,
        height: b.height * hlRatio,
        fill: color,
        rx: 2, ry: 2,
        selectable: false,
        evented: false,
        _isHL: true,
    });
    canvas.add(rect);
    var idx = canvas.getObjects().indexOf(textObj);
    canvas.moveTo(rect, idx);
    textObj._hlRect = rect;
    textObj._hlEnabled = true;
    textObj._hlColor = color;
    textObj._hlThickness = thickness;
    canvas.renderAll();
}

function removeHL(textObj) {
    if (textObj._hlRect) {
        canvas.remove(textObj._hlRect);
        textObj._hlRect = null;
        textObj._hlEnabled = false;
        canvas.renderAll();
    }
}

function syncHL(textObj) {
    if (textObj._hlRect) {
        var b = getTextBounds(textObj);
        var hlRatio = (textObj._hlThickness || 40) / 100;
        textObj._hlRect.set({
            left: b.left - 8,
            top: b.top + b.height * (1 - hlRatio),
            width: b.width + 16,
            height: b.height * hlRatio,
        });
        textObj._hlRect.setCoords();
        canvas.renderAll();
    }
}

// ═══════════════════════════════════════
// 브러시 선 (손그림 느낌 구분선)
// ═══════════════════════════════════════
function addBrushLine(opts) {
    opts = opts || {};
    var y = opts.y || CH * 0.58;
    var x1 = opts.x1 || CW * 0.12;
    var x2 = opts.x2 || CW * 0.88;
    var color = opts.color || PRESETS[currentPreset].hl;

    var midX = (x1 + x2) / 2;
    var path = new fabric.Path(
        'M ' + x1 + ' ' + y +
        ' Q ' + (x1 + (midX - x1) * 0.3) + ' ' + (y - 4) +
        ' ' + midX + ' ' + (y + 2) +
        ' Q ' + (midX + (x2 - midX) * 0.7) + ' ' + (y + 6) +
        ' ' + x2 + ' ' + (y - 1),
        {
            stroke: color,
            strokeWidth: opts.strokeWidth || 8,
            fill: '',
            strokeLineCap: 'round',
            selectable: true,
            _etype: 'brushline',
        }
    );
    canvas.add(path);
    return path;
}

// ═══════════════════════════════════════
// 덕테이프 / 마스킹테이프 장식
// ═══════════════════════════════════════
function addDuctTape(opts) {
    opts = opts || {};
    var w = opts.width || Math.min(CW * 0.34, 360);
    var h = opts.height || 58;
    var tooth = Math.max(7, Math.round(h * 0.18));
    var color = opts.color || '#d9d3c1';
    var edge = opts.edge || 'rgba(94, 83, 67, 0.22)';
    var opacity = opts.opacity || 0.9;

    var points = [
        {x: 0, y: tooth},
        {x: tooth * 0.9, y: 0},
        {x: w - tooth * 0.7, y: 0},
        {x: w, y: tooth * 0.85},
        {x: w - tooth * 0.45, y: h * 0.34},
        {x: w, y: h * 0.58},
        {x: w - tooth * 0.75, y: h},
        {x: tooth * 0.7, y: h},
        {x: 0, y: h - tooth},
        {x: tooth * 0.45, y: h * 0.62},
        {x: 0, y: h * 0.36},
    ];

    var body = new fabric.Polygon(points, {
        left: 0,
        top: 0,
        fill: color,
        stroke: edge,
        strokeWidth: 1,
        opacity: opacity,
        objectCaching: false,
    });

    var fibers = [];
    for (var x = 12; x < w - 12; x += 28) {
        fibers.push(new fabric.Line([x, h - 5, x + h * 0.45, 5], {
            stroke: 'rgba(255,255,255,0.28)',
            strokeWidth: 2,
            opacity: 0.8,
            selectable: false,
            evented: false,
        }));
    }
    fibers.push(new fabric.Line([w * 0.08, h * 0.32, w * 0.92, h * 0.26], {
        stroke: 'rgba(92, 72, 52, 0.16)',
        strokeWidth: 1,
        selectable: false,
        evented: false,
    }));
    fibers.push(new fabric.Line([w * 0.1, h * 0.68, w * 0.9, h * 0.72], {
        stroke: 'rgba(92, 72, 52, 0.12)',
        strokeWidth: 1,
        selectable: false,
        evented: false,
    }));

    var group = new fabric.Group([body].concat(fibers), {
        left: (opts.left || CW / 2) - w / 2,
        top: (opts.top || CH / 2) - h / 2,
        angle: opts.angle || -5,
        _etype: 'tape',
        objectCaching: false,
    });
    canvas.add(group);
    return group;
}

// ═══════════════════════════════════════
// 초기 요소 생성 (기본 템플릿 사용)
// ═══════════════════════════════════════
function initElements() {
    var p = PRESETS[currentPreset];
    TEMPLATES[currentTemplate].build(p);
    canvas.renderAll();
    saveState();
}

// 폰트 로딩 후 초기화
Promise.race([
    document.fonts.ready,
    new Promise(function(r) { setTimeout(r, 3000); })
]).then(initElements);

// ═══════════════════════════════════════
// 선택 요소 속성 패널
// ═══════════════════════════════════════
var propBar = document.getElementById('propBar');
var textProps = document.getElementById('textProps');
var shapeProps = document.getElementById('shapeProps');

canvas.on('selection:created', function(e) { showProps(e.selected[0]); });
canvas.on('selection:updated', function(e) { showProps(e.selected[0]); });
canvas.on('selection:cleared', function() { propBar.style.display = 'none'; });

function showProps(obj) {
    if (!obj || obj._isHL || obj._isGrid) return;
    propBar.style.display = 'flex';

    var types = { title:'제목', subtitle:'부제목', category:'카테고리', branding:'푸터', separator:'구분선', brushline:'브러시선', tape:'덕테이프', decoration:'장식', custom:'텍스트', shape:'도형', circle:'원형' };
    document.getElementById('selected-info').textContent = (types[obj._etype] || obj.type) + ' 선택됨';

    var isText = (obj.type === 'i-text' || obj.type === 'text');
    var isShape = (obj.type === 'rect' || obj.type === 'circle' || obj.type === 'ellipse');

    textProps.style.display = isText ? 'flex' : 'none';
    shapeProps.style.display = isShape ? 'flex' : 'none';

    // 공통: 투명도
    document.getElementById('opacityRange').value = Math.round((obj.opacity || 1) * 100);
    document.getElementById('opacityLabel').textContent = Math.round((obj.opacity || 1) * 100);

    // 잠금 상태
    document.getElementById('lockBtn').textContent = obj._locked ? '🔓' : '🔒';

    if (isText) {
        document.getElementById('textColor').value = toHex(obj.fill || '#000000');
        document.getElementById('fontSize').value = obj.fontSize || 80;
        document.getElementById('fontSizeLabel').textContent = (obj.fontSize || 80);
        document.getElementById('hlToggle').checked = !!obj._hlEnabled;
        document.getElementById('hlColor').value = toHex(obj._hlColor || PRESETS[currentPreset].hl);
        document.getElementById('hlThickness').value = obj._hlThickness || 40;
        document.getElementById('hlThicknessLabel').textContent = obj._hlThickness || 40;
        document.getElementById('fontSelect').value = obj.fontFamily || 'Cafe24Dangdanghae';
        document.getElementById('fontWeight').value = String(obj.fontWeight || '700');

        // 정렬 버튼 활성화
        var align = obj.textAlign || 'center';
        document.getElementById('alignLeft').classList.toggle('active', align === 'left');
        document.getElementById('alignCenter').classList.toggle('active', align === 'center');
        document.getElementById('alignRight').classList.toggle('active', align === 'right');

        // 그림자
        document.getElementById('shadowToggle').checked = !!obj.shadow;
        // 외곽선
        document.getElementById('strokeToggle').checked = !!obj.strokeWidth && obj.strokeWidth > 0 && !!obj.stroke;
        if (obj.stroke) document.getElementById('strokeColor').value = toHex(obj.stroke);
        document.getElementById('strokeWidth').value = obj.strokeWidth || 2;
        document.getElementById('strokeWidthLabel').textContent = obj.strokeWidth || 2;
    }

    if (isShape) {
        document.getElementById('shapeFill').value = toHex(obj.fill || '#E8967D');
        document.getElementById('shapeStroke').value = toHex(obj.stroke || '#E8967D');
        document.getElementById('shapeStrokeW').value = obj.strokeWidth || 0;
        document.getElementById('shapeStrokeWLabel').textContent = obj.strokeWidth || 0;
        if (obj.rx !== undefined) {
            document.getElementById('shapeRadius').value = obj.rx || 0;
            document.getElementById('shapeRadiusLabel').textContent = obj.rx || 0;
        }
    }
}

// ── 텍스트 속성 핸들러 ──

document.getElementById('textColor').oninput = function() {
    var obj = canvas.getActiveObject();
    if (obj && (obj.type === 'i-text' || obj.type === 'text')) {
        obj.set('fill', this.value);
        canvas.renderAll();
    }
};

document.getElementById('fontSelect').onchange = function() {
    var obj = canvas.getActiveObject();
    if (obj && (obj.type === 'i-text' || obj.type === 'text')) {
        obj.set('fontFamily', this.value);
        canvas.renderAll();
        setTimeout(function() { syncHL(obj); saveState(); }, 50);
    }
};

document.getElementById('fontSize').oninput = function() {
    var obj = canvas.getActiveObject();
    document.getElementById('fontSizeLabel').textContent = this.value;
    if (obj && (obj.type === 'i-text' || obj.type === 'text')) {
        obj.set('fontSize', parseInt(this.value));
        canvas.renderAll();
        syncHL(obj);
    }
};
document.getElementById('fontSize').onchange = function() { saveState(); };

document.getElementById('fontWeight').onchange = function() {
    var obj = canvas.getActiveObject();
    if (obj && (obj.type === 'i-text' || obj.type === 'text')) {
        obj.set('fontWeight', this.value);
        canvas.renderAll();
        syncHL(obj);
        saveState();
    }
};

// 정렬
['Left','Center','Right'].forEach(function(dir) {
    document.getElementById('align' + dir).onclick = function() {
        var obj = canvas.getActiveObject();
        if (!obj || (obj.type !== 'i-text' && obj.type !== 'text')) return;
        var align = dir.toLowerCase();
        obj.set('textAlign', align);
        if (align === 'left') { obj.set('originX', 'left'); obj.set('left', 60); }
        else if (align === 'right') { obj.set('originX', 'right'); obj.set('left', CW - 60); }
        else { obj.set('originX', 'center'); obj.set('left', CW / 2); }

        document.getElementById('alignLeft').classList.toggle('active', align === 'left');
        document.getElementById('alignCenter').classList.toggle('active', align === 'center');
        document.getElementById('alignRight').classList.toggle('active', align === 'right');
        canvas.renderAll();
        syncHL(obj);
        saveState();
    };
});

// 형광펜
document.getElementById('hlToggle').onchange = function() {
    var obj = canvas.getActiveObject();
    if (!obj || obj._isHL) return;
    if (this.checked) {
        addHL(obj, document.getElementById('hlColor').value, parseInt(document.getElementById('hlThickness').value));
    } else {
        removeHL(obj);
    }
    saveState();
};

document.getElementById('hlColor').oninput = function() {
    var obj = canvas.getActiveObject();
    if (obj && obj._hlEnabled && obj._hlRect) {
        obj._hlColor = this.value;
        obj._hlRect.set('fill', this.value);
        canvas.renderAll();
    }
};
document.getElementById('hlColor').onchange = function() { saveState(); };

document.getElementById('hlThickness').oninput = function() {
    var obj = canvas.getActiveObject();
    document.getElementById('hlThicknessLabel').textContent = this.value;
    if (obj && obj._hlEnabled) {
        obj._hlThickness = parseInt(this.value);
        syncHL(obj);
    }
};
document.getElementById('hlThickness').onchange = function() { saveState(); };

// ── 텍스트 그림자 ──
document.getElementById('shadowToggle').onchange = function() {
    var obj = canvas.getActiveObject();
    if (!obj || (obj.type !== 'i-text' && obj.type !== 'text')) return;
    if (this.checked) {
        obj.set('shadow', new fabric.Shadow({ color: 'rgba(0,0,0,0.3)', blur: 8, offsetX: 3, offsetY: 3 }));
    } else {
        obj.set('shadow', null);
    }
    canvas.renderAll();
    saveState();
};

// ── 텍스트 외곽선 ──
document.getElementById('strokeToggle').onchange = function() {
    var obj = canvas.getActiveObject();
    if (!obj || (obj.type !== 'i-text' && obj.type !== 'text')) return;
    if (this.checked) {
        obj.set('stroke', document.getElementById('strokeColor').value);
        obj.set('strokeWidth', parseInt(document.getElementById('strokeWidth').value));
    } else {
        obj.set('stroke', null);
        obj.set('strokeWidth', 0);
    }
    canvas.renderAll();
    saveState();
};

document.getElementById('strokeColor').oninput = function() {
    var obj = canvas.getActiveObject();
    if (obj && obj.stroke) {
        obj.set('stroke', this.value);
        canvas.renderAll();
    }
};
document.getElementById('strokeColor').onchange = function() { saveState(); };

document.getElementById('strokeWidth').oninput = function() {
    var obj = canvas.getActiveObject();
    document.getElementById('strokeWidthLabel').textContent = this.value;
    if (obj && obj.stroke) {
        obj.set('strokeWidth', parseInt(this.value));
        canvas.renderAll();
    }
};
document.getElementById('strokeWidth').onchange = function() { saveState(); };

// ── 도형 속성 핸들러 ──

document.getElementById('shapeFill').oninput = function() {
    var obj = canvas.getActiveObject();
    if (obj && (obj.type === 'rect' || obj.type === 'circle' || obj.type === 'ellipse')) {
        obj.set('fill', this.value);
        canvas.renderAll();
    }
};
document.getElementById('shapeFill').onchange = function() { saveState(); };

document.getElementById('shapeStroke').oninput = function() {
    var obj = canvas.getActiveObject();
    if (obj) { obj.set('stroke', this.value); canvas.renderAll(); }
};
document.getElementById('shapeStroke').onchange = function() { saveState(); };

document.getElementById('shapeStrokeW').oninput = function() {
    var obj = canvas.getActiveObject();
    document.getElementById('shapeStrokeWLabel').textContent = this.value;
    if (obj) { obj.set('strokeWidth', parseInt(this.value)); canvas.renderAll(); }
};
document.getElementById('shapeStrokeW').onchange = function() { saveState(); };

document.getElementById('shapeRadius').oninput = function() {
    var obj = canvas.getActiveObject();
    document.getElementById('shapeRadiusLabel').textContent = this.value;
    if (obj && obj.type === 'rect') {
        obj.set({ rx: parseInt(this.value), ry: parseInt(this.value) });
        canvas.renderAll();
    }
};
document.getElementById('shapeRadius').onchange = function() { saveState(); };

// ── 공통 속성 핸들러 ──

// 투명도
document.getElementById('opacityRange').oninput = function() {
    var obj = canvas.getActiveObject();
    document.getElementById('opacityLabel').textContent = this.value;
    if (obj) {
        obj.set('opacity', parseInt(this.value) / 100);
        canvas.renderAll();
    }
};
document.getElementById('opacityRange').onchange = function() { saveState(); };

// Z-index
document.getElementById('bringFrontBtn').onclick = function() {
    var obj = canvas.getActiveObject();
    if (obj) { canvas.bringToFront(obj); canvas.renderAll(); saveState(); }
};
document.getElementById('bringUpBtn').onclick = function() {
    var obj = canvas.getActiveObject();
    if (obj) { canvas.bringForward(obj); canvas.renderAll(); saveState(); }
};
document.getElementById('sendDownBtn').onclick = function() {
    var obj = canvas.getActiveObject();
    if (obj) { canvas.sendBackwards(obj); canvas.renderAll(); saveState(); }
};
document.getElementById('sendBackBtn').onclick = function() {
    var obj = canvas.getActiveObject();
    if (obj) { canvas.sendToBack(obj); canvas.renderAll(); saveState(); }
};

// 복제
document.getElementById('duplicateBtn').onclick = function() { duplicateSelected(); };

function duplicateSelected() {
    var obj = canvas.getActiveObject();
    if (!obj) return;
    obj.clone(function(cloned) {
        cloned.set({ left: obj.left + 30, top: obj.top + 30 });
        if (cloned._isHL) return;
        canvas.add(cloned);
        if (cloned.type === 'i-text') bindHLEvents(cloned);
        canvas.setActiveObject(cloned);
        canvas.renderAll();
        saveState();
    }, ['_etype','_hlEnabled','_hlColor','_hlThickness','_isHL','_locked']);
}

// 잠금
document.getElementById('lockBtn').onclick = function() {
    var obj = canvas.getActiveObject();
    if (!obj) return;
    var locked = !obj._locked;
    obj._locked = locked;
    obj.set({
        lockMovementX: locked,
        lockMovementY: locked,
        lockScalingX: locked,
        lockScalingY: locked,
        lockRotation: locked,
        hasControls: !locked,
    });
    this.textContent = locked ? '🔓' : '🔒';
    canvas.renderAll();
};

// 삭제
document.getElementById('deleteBtn').onclick = function() { deleteSelected(); };

function deleteSelected() {
    var obj = canvas.getActiveObject();
    if (obj) {
        if (obj._hlRect) removeHL(obj);
        canvas.remove(obj);
        canvas.discardActiveObject();
        canvas.renderAll();
        saveState();
    }
}

// ═══════════════════════════════════════
// 요소 추가 버튼
// ═══════════════════════════════════════

// 텍스트 추가
document.getElementById('addTextBtn').onclick = function() {
    var t = createText('새 텍스트', {
        left: CW / 2, top: CH / 2,
        fontFamily: 'Cafe24Dangdanghae',
        fontSize: 48, fontWeight: '400',
        fill: PRESETS[currentPreset].text,
        etype: 'custom',
    });
    canvas.setActiveObject(t);
    showProps(t);
    saveState();
};

// 사각형 추가
document.getElementById('addRectBtn').onclick = function() {
    var rect = new fabric.Rect({
        left: CW / 2 - 100, top: CH / 2 - 60,
        width: 200, height: 120,
        fill: PRESETS[currentPreset].hl + '80',
        rx: 10, ry: 10,
        stroke: '', strokeWidth: 0,
        _etype: 'shape',
    });
    canvas.add(rect);
    canvas.setActiveObject(rect);
    showProps(rect);
    saveState();
};

// 원형 추가
document.getElementById('addCircleBtn').onclick = function() {
    var circle = new fabric.Circle({
        left: CW / 2 - 60, top: CH / 2 - 60,
        radius: 60,
        fill: PRESETS[currentPreset].hl + '80',
        stroke: '', strokeWidth: 0,
        _etype: 'circle',
    });
    canvas.add(circle);
    canvas.setActiveObject(circle);
    showProps(circle);
    saveState();
};

// 구분선 추가
document.getElementById('addLineBtn').onclick = function() {
    var line = new fabric.Line([CW * 0.15, CH / 2, CW * 0.85, CH / 2], {
        stroke: PRESETS[currentPreset].brand,
        strokeWidth: 3,
        selectable: true,
        _etype: 'separator',
    });
    canvas.add(line);
    canvas.setActiveObject(line);
    canvas.renderAll();
    saveState();
};

// 브러시 선 추가
document.getElementById('addBrushLineBtn').onclick = function() {
    var bl = addBrushLine({ y: CH / 2, color: PRESETS[currentPreset].hl, strokeWidth: 8 });
    canvas.setActiveObject(bl);
    canvas.renderAll();
    saveState();
};

// 덕테이프 추가
document.getElementById('addTapeBtn').onclick = function() {
    var tape = addDuctTape({
        left: CW / 2,
        top: CH / 2,
        width: Math.min(CW * 0.34, 360),
        height: 58,
        angle: -6,
    });
    canvas.setActiveObject(tape);
    canvas.renderAll();
    saveState();
};

// 이미지 업로드
document.getElementById('imgUploadBtn').onclick = function() {
    document.getElementById('imgUploadInput').click();
};

document.getElementById('imgUploadInput').onchange = function(e) {
    var file = e.target.files[0];
    if (!file) return;
    var reader = new FileReader();
    reader.onload = function(ev) {
        fabric.Image.fromURL(ev.target.result, function(img) {
            var maxDim = Math.min(CW, CH) * 0.5;
            var sc = Math.min(maxDim / img.width, maxDim / img.height, 1);
            img.scale(sc);
            img.set({ left: CW / 2, top: CH / 2, originX: 'center', originY: 'center', _etype: 'image' });
            canvas.add(img);
            canvas.setActiveObject(img);
            canvas.renderAll();
            saveState();
        });
    };
    reader.readAsDataURL(file);
    this.value = '';
};

// ═══════════════════════════════════════
// 배경 이미지
// ═══════════════════════════════════════
document.getElementById('bgImgBtn').onclick = function() {
    document.getElementById('bgImgInput').click();
};

document.getElementById('bgImgInput').onchange = function(e) {
    var file = e.target.files[0];
    if (!file) return;
    var reader = new FileReader();
    reader.onload = function(ev) {
        fabric.Image.fromURL(ev.target.result, function(img) {
            var scaleX = CW / img.width;
            var scaleY = CH / img.height;
            var sc = Math.max(scaleX, scaleY);
            img.set({ scaleX: sc, scaleY: sc, originX: 'center', originY: 'center', left: CW / 2, top: CH / 2 });
            canvas.setBackgroundImage(img, function() {
                canvas.renderAll();
                saveState();
            });
        });
    };
    reader.readAsDataURL(file);
    this.value = '';
    document.getElementById('bgImgClearBtn').style.display = 'inline-block';
};

document.getElementById('bgImgClearBtn').onclick = function() {
    canvas.setBackgroundImage(null, function() {
        canvas.renderAll();
        saveState();
    });
    this.style.display = 'none';
};

// ═══════════════════════════════════════
// 키보드 단축키
// ═══════════════════════════════════════
document.addEventListener('keydown', function(e) {
    var obj = canvas.getActiveObject();

    // Delete/Backspace (편집 중 아닐 때)
    if ((e.key === 'Delete' || e.key === 'Backspace') && obj && !obj.isEditing) {
        e.preventDefault();
        deleteSelected();
        return;
    }

    // Ctrl+D: 복제
    if ((e.ctrlKey || e.metaKey) && e.key === 'd') {
        e.preventDefault();
        duplicateSelected();
        return;
    }

    // Ctrl+Z: 되돌리기
    if ((e.ctrlKey || e.metaKey) && !e.shiftKey && e.key === 'z') {
        e.preventDefault();
        undo();
        return;
    }

    // Ctrl+Shift+Z: 다시실행 (Redo)
    if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'z') {
        e.preventDefault();
        redo();
        return;
    }

    // Ctrl+Y: 다시실행 (Redo 대체키)
    if ((e.ctrlKey || e.metaKey) && e.key === 'y') {
        e.preventDefault();
        redo();
        return;
    }
});

// ═══════════════════════════════════════
// 캔버스 사이즈 변경
// ═══════════════════════════════════════
document.getElementById('canvasSize').onchange = function() {
    var parts = this.value.split('x');
    CW = parseInt(parts[0]);
    CH = parseInt(parts[1]);
    var maxW = Math.min(document.documentElement.clientWidth - 50, 900);
    var maxH = 600;
    scale = Math.min(maxW / CW, maxH / CH);
    canvas.setZoom(scale);
    canvas.setWidth(CW * scale);
    canvas.setHeight(CH * scale);
    canvas.renderAll();
};

// 배경색
document.getElementById('bgColor').oninput = function() {
    canvas.setBackgroundColor(this.value, function() { canvas.renderAll(); });
};
document.getElementById('bgColor').onchange = function() { saveState(); };

// ═══════════════════════════════════════
// 다운로드
// ═══════════════════════════════════════
document.getElementById('downloadBtn').onclick = function() {
    canvas.discardActiveObject();
    canvas.renderAll();

    // 그리드 숨기기
    var wasGrid = gridVisible;
    if (wasGrid) { gridVisible = false; removeGrid(); }

    var origZoom = canvas.getZoom();
    var origW = canvas.getWidth();
    var origH = canvas.getHeight();

    canvas.setZoom(1);
    canvas.setWidth(CW);
    canvas.setHeight(CH);
    canvas.renderAll();

    var dataURL = canvas.toDataURL({ format: 'png', multiplier: 1 });
    var a = document.createElement('a');
    a.href = dataURL;
    a.download = 'thumbnail_' + Date.now() + '.png';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);

    canvas.setZoom(origZoom);
    canvas.setWidth(origW);
    canvas.setHeight(origH);

    // 그리드 복원
    if (wasGrid) { gridVisible = true; drawGrid(); }
    canvas.renderAll();
};

// ═══════════════════════════════════════
// 유틸리티
// ═══════════════════════════════════════
function toHex(color) {
    if (!color) return '#000000';
    if (color.startsWith('#')) return color.substring(0, 7);
    var m = color.match(/\d+/g);
    if (!m || m.length < 3) return '#000000';
    return '#' + [m[0],m[1],m[2]].map(function(x) {
        return parseInt(x).toString(16).padStart(2,'0');
    }).join('');
}
</script>
</body>
</html>
""".replace("__CONFIG_JSON__", config_json)

st.components.v1.html(CANVAS_HTML, height=820, scrolling=False)

st.caption("💡 팁: 더블클릭으로 텍스트 편집 · 드래그로 이동 · 모서리 드래그로 크기 조절 · Ctrl+D 복제 · Ctrl+Z 되돌리기 · Ctrl+Shift+Z 다시실행")
