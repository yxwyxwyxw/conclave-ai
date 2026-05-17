APP_HTML = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>命理裁决台 · 天机秘册</title>
<style>
  :root {
    --bg-start: #1e1813;
    --bg-end: #120e0a;
    --bg-card: rgba(20, 16, 12, 0.65);
    --bg-input: rgba(10, 8, 5, 0.5);
    --border: rgba(212, 165, 116, 0.15);
    --border-hover: rgba(212, 165, 116, 0.35);
    --text: #d4c5b0;
    --text-dim: #8b7355;
    --text-bright: #f0e6d8;
    --gold: #d4a574;
    --gold-light: #e6b584;
    --gold-dim: #a89050;
    --green: #6baf7a;
    --amber: #d4a574;
    --red: #c47a6a;
    --purple: #b388ff;
    --radius: 8px;
    --font: "方正仿宋_GB2312", "仿宋", "FangSong", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
  }

  * { box-sizing: border-box; margin: 0; padding: 0; }

  ::-webkit-scrollbar { width: 10px; }
  ::-webkit-scrollbar-track { background: rgba(20, 18, 15, 0.3); border-radius: 8px; }
  ::-webkit-scrollbar-thumb {
    background: linear-gradient(180deg, var(--gold) 0%, var(--gold-dim) 50%, var(--gold) 100%);
    border-radius: 8px; border: 2px solid rgba(20, 18, 15, 0.6);
    box-shadow: 0 0 6px rgba(212, 165, 116, 0.3);
  }
  ::-webkit-scrollbar-thumb:hover { background: linear-gradient(180deg, var(--gold-light) 0%, var(--gold) 100%); }
  * { scrollbar-color: var(--gold) rgba(20, 18, 15, 0.3); scrollbar-width: thin; }

  html { background: var(--bg-end); }

  body {
    font-family: var(--font);
    color: var(--text);
    background: radial-gradient(ellipse at 20% 20%, rgba(212,165,116,0.06) 0%, transparent 55%),
                radial-gradient(ellipse at 80% 80%, rgba(212,165,116,0.04) 0%, transparent 55%),
                linear-gradient(180deg, var(--bg-start) 0%, var(--bg-end) 50%, var(--bg-start) 100%);
    min-height: 100vh;
    -webkit-font-smoothing: antialiased;
    position: relative;
    overflow-x: hidden;
  }

  /* ── decorative background circles ── */
  .deco-bg {
    position: fixed; top: 0; left: 0; width: 100%; height: 100%;
    z-index: 1; pointer-events: none; overflow: hidden;
  }
  .deco-ring {
    position: absolute; border-radius: 50%;
  }
  .deco-ring:nth-child(1) {
    width: 500px; height: 500px; top: 50%; left: 50%;
    border: 1px solid rgba(212, 165, 116, 0.08);
    transform: translate(-50%, -50%);
    animation: ringSpin 30s linear infinite;
  }
  .deco-ring:nth-child(2) {
    width: 700px; height: 700px; top: 50%; left: 50%;
    border: 1px solid rgba(139, 115, 85, 0.06);
    transform: translate(-50%, -50%);
    animation: ringSpin 45s linear infinite reverse;
  }
  .deco-ring:nth-child(3) {
    width: 300px; height: 300px; top: 50%; left: 50%;
    border: 1px solid rgba(212, 165, 116, 0.04);
    transform: translate(-50%, -50%);
    animation: ringSpin 20s linear infinite;
  }
  @keyframes ringSpin { from { transform: translate(-50%, -50%) rotate(0deg); } to { transform: translate(-50%, -50%) rotate(360deg); } }

  /* ── ink particles ── */
  .ink-layer {
    position: fixed; top: 0; left: 0; width: 100%; height: 100%;
    z-index: 2; pointer-events: none; overflow: hidden;
  }
  .ink-dot {
    position: absolute; border-radius: 50%; opacity: 0.06;
    filter: blur(2px);
    animation: inkFloat linear infinite;
  }
  @keyframes inkFloat {
    0%   { transform: translateY(0) translateX(0); opacity: 0.06; }
    50%  { opacity: 0.12; }
    100% { transform: translateY(-100vh) translateX(80px); opacity: 0; }
  }

  /* ── cursor particles ── */
  .cursor-spark {
    position: fixed; pointer-events: none; z-index: 9999;
    font-size: 14px; opacity: 0;
    animation: sparkFloat 0.8s ease-out forwards;
  }
  @keyframes sparkFloat {
    0%   { opacity: 1; transform: translate(0,0) scale(1); }
    100% { opacity: 0; transform: translate(var(--tx), var(--ty)) scale(0); }
  }

  /* ── hero / login circle ── */
  .hero-screen {
    position: fixed; top: 0; left: 0; width: 100%; height: 100%;
    z-index: 50; display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    transition: opacity 0.8s ease, transform 0.8s ease;
  }
  .hero-screen.hidden {
    opacity: 0; transform: scale(0.9); pointer-events: none;
  }

  .hero-circle {
    width: 220px; height: 220px; cursor: pointer; position: relative;
    filter: drop-shadow(0 0 40px rgba(212, 165, 116, 0.2));
    transition: transform 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
    animation: heroPulse 4s ease-in-out infinite;
  }
  .hero-circle:hover { transform: scale(1.04); }
  .hero-circle:active { transform: scale(0.96); }

  @keyframes heroPulse {
    0%, 100% { filter: drop-shadow(0 0 30px rgba(212, 165, 116, 0.15)); }
    50% { filter: drop-shadow(0 0 50px rgba(212, 165, 116, 0.30)); }
  }

  .hero-circle svg { width: 100%; height: 100%; }

  .hero-title {
    color: var(--gold); font-size: 28px; letter-spacing: 8px;
    margin-top: 36px; font-weight: 400;
    text-shadow: 0 2px 12px rgba(0,0,0,0.8), 0 0 40px rgba(212,165,116,0.2);
  }
  .hero-sub {
    color: var(--text-dim); font-size: 13px; letter-spacing: 4px;
    margin-top: 10px; font-style: italic;
  }
  .hero-hint {
    color: rgba(212, 165, 116, 0.4); font-size: 12px; letter-spacing: 2px;
    margin-top: 20px; animation: hintBlink 2s ease-in-out infinite;
  }
  @keyframes hintBlink { 0%,100% { opacity: 0.3; } 50% { opacity: 0.7; } }

  /* ── inline password after circle click ── */
  .hero-password {
    margin-top: 24px; display: none; animation: pwSlideIn 0.4s ease both;
  }
  .hero-password.show { display: flex; align-items: center; gap: 10px; }
  @keyframes pwSlideIn {
    from { opacity: 0; transform: translateY(-10px); }
    to   { opacity: 1; transform: translateY(0); }
  }
  .hero-password input {
    background: rgba(10,8,5,0.6); border: 1px solid var(--border);
    border-radius: 50px; padding: 12px 20px; width: 200px;
    font-size: 14px; color: var(--gold); font-family: inherit;
    text-align: center; letter-spacing: 2px; outline: none;
    transition: border-color 0.3s;
    backdrop-filter: blur(8px);
  }
  .hero-password input:focus { border-color: var(--gold); box-shadow: 0 0 20px rgba(212,165,116,0.15); }
  .hero-password input::placeholder { color: rgba(212,165,116,0.25); letter-spacing: 1px; }
  .hero-password button {
    background: linear-gradient(135deg, rgba(212,165,116,0.15), rgba(200,152,96,0.10));
    border: 1px solid rgba(212,165,116,0.3); border-radius: 50px;
    padding: 12px 24px; color: var(--gold); font-size: 14px; cursor: pointer;
    font-family: inherit; letter-spacing: 2px;
    transition: all 0.25s;
  }
  .hero-password button:hover { background: linear-gradient(135deg, rgba(222,181,135,0.25), rgba(212,165,116,0.15)); border-color: var(--gold); }

  .hero-err {
    color: var(--red); font-size: 12px; margin-top: 12px; display: none;
  }

  /* ── general ── */
  button, input, textarea, select { font: inherit; }
  input, textarea, select {
    background: var(--bg-input); border: 1px solid var(--border);
    border-radius: var(--radius); padding: 10px 14px; font-size: 14px;
    transition: all 0.25s ease; width: 100%;
    backdrop-filter: blur(4px);
    color: var(--text);
  }
  input:focus, textarea:focus, select:focus {
    outline: none; border-color: var(--gold);
    background: rgba(20, 15, 10, 0.6);
    box-shadow: 0 0 16px rgba(212, 165, 116, 0.12), inset 0 1px 4px rgba(0,0,0,0.2);
    transform: scale(1.01);
  }
  textarea { min-height: 68px; resize: vertical; }
  label { display: flex; flex-direction: column; gap: 5px; font-size: 12px; color: var(--text-dim); letter-spacing: 0.06em; }

  button {
    cursor: pointer; border: 1px solid var(--border); background: var(--bg-card);
    padding: 10px 22px; border-radius: 50px; font-size: 14px; font-weight: 600;
    transition: all 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
    letter-spacing: 0.06em; position: relative; overflow: hidden;
    backdrop-filter: blur(8px);
    color: var(--text);
  }
  button::before {
    content: ''; position: absolute; top: 50%; left: 50%;
    width: 0; height: 0; border-radius: 50%;
    background: rgba(212, 165, 116, 0.15);
    transform: translate(-50%, -50%);
    transition: width 0.5s, height 0.5s;
  }
  button:hover {
    border-color: var(--gold); background: rgba(40, 32, 25, 0.7);
    transform: translateY(-2px);
    box-shadow: 0 6px 24px rgba(212, 165, 116, 0.15);
  }
  button:hover::before { width: 300px; height: 300px; }
  button:active { transform: translateY(0) scale(0.97); }
  button.primary {
    border-color: rgba(212, 165, 116, 0.4);
    background: linear-gradient(135deg, rgba(212,165,116,0.15) 0%, rgba(200,152,96,0.10) 100%);
    color: var(--gold);
    box-shadow: 0 4px 20px rgba(212, 165, 116, 0.08);
  }
  button.primary:hover {
    background: linear-gradient(135deg, rgba(222,181,135,0.20) 0%, rgba(212,165,116,0.15) 100%);
    border-color: var(--gold);
    box-shadow: 0 8px 32px rgba(212, 165, 116, 0.20);
  }
  button:focus-visible, input:focus-visible, textarea:focus-visible, select:focus-visible {
    outline: none; border-color: var(--gold);
    box-shadow: 0 0 0 2px rgba(212, 165, 116, 0.15);
  }

  /* ── card entrance ── */
  @keyframes cardSlideIn {
    from { opacity: 0; transform: translateX(-30px) rotateY(8deg); }
    to   { opacity: 1; transform: translateX(0) rotateY(0); }
  }
  .card {
    border: 1px solid var(--border); border-radius: var(--radius);
    background: var(--bg-card); padding: 22px;
    backdrop-filter: blur(12px);
    box-shadow: 0 4px 24px rgba(0,0,0,0.15);
    animation: cardSlideIn 0.5s cubic-bezier(0.34, 1.56, 0.64, 1) both;
    position: relative; overflow: hidden;
    transition: border-color 0.3s;
  }
  .card:hover { border-color: rgba(212, 165, 116, 0.20); }
  .card::before {
    content: ''; position: absolute; top: -1px; left: -100%;
    width: 60%; height: 2px;
    background: linear-gradient(90deg, transparent, rgba(212, 165, 116, 0.3), transparent);
    animation: cardShine 4s ease-in-out infinite;
  }
  @keyframes cardShine {
    0%, 100% { left: -100%; } 50% { left: 100%; }
  }
  .card:nth-child(2) { animation-delay: 0.08s; }
  .card:nth-child(3) { animation-delay: 0.16s; }
  .card:nth-child(4) { animation-delay: 0.24s; }

  .container { max-width: 920px; margin: 0 auto; padding: 40px 20px; display: grid; gap: 20px; position: relative; z-index: 10; }

  .header {
    display: flex; align-items: center; justify-content: space-between;
    padding-bottom: 18px; border-bottom: 1px solid rgba(212, 165, 116, 0.10);
    animation: cardSlideIn 0.4s cubic-bezier(0.34, 1.56, 0.64, 1) both;
  }
  .logo { font-size: 20px; font-weight: 700; letter-spacing: 0.08em; color: var(--text-bright); }
  .logo em { font-style: normal; color: var(--gold); text-shadow: 0 0 20px rgba(212, 165, 116, 0.25); }
  .logo small { font-size: 12px; color: var(--text-dim); margin-left: 6px; letter-spacing: 0.12em; }

  .card-title {
    font-size: 12px; font-weight: 700; color: var(--text-dim);
    letter-spacing: 0.08em; margin-bottom: 14px;
    display: flex; align-items: center; gap: 8px;
  }
  .card-title::before { content: "◆"; font-size: 8px; color: var(--gold); }

  .form-grid { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px; }
  .form-grid .wide { grid-column: span 2; }

  .pill {
    display: inline-flex; align-items: center; gap: 6px; padding: 3px 12px;
    border-radius: 99px; font-size: 11px; font-weight: 600; letter-spacing: 0.04em;
    border: 1px solid var(--border); backdrop-filter: blur(4px);
    color: var(--text-dim);
  }
  .pill::before { content: ""; width: 5px; height: 5px; border-radius: 50%; }
  .pill.idle::before { background: var(--text-dim); }
  .pill.running { color: var(--amber); } .pill.running::before { background: var(--amber); box-shadow: 0 0 6px var(--amber); }
  .pill.done { color: var(--green); } .pill.done::before { background: var(--green); }
  .pill.failed { color: var(--red); } .pill.failed::before { background: var(--red); }

  .report-text { font-size: 15px; line-height: 1.85; color: var(--text); white-space: pre-wrap; }
  .report-text h3 { font-size: 16px; color: var(--gold); margin: 20px 0 8px; }
  .report-text strong { color: var(--text-bright); }

  .issue-item { border: 1px solid var(--border); border-radius: var(--radius); margin-bottom: 10px; overflow: hidden; background: rgba(20, 18, 15, 0.2); }
  .issue-head {
    display: flex; align-items: center; justify-content: space-between;
    padding: 14px 16px; cursor: pointer; user-select: none;
  }
  .issue-head:hover { background: rgba(212, 165, 116, 0.02); }
  .issue-body { padding: 0 16px 16px; display: none; }
  .issue-item.open .issue-body { display: block; }

  .tag {
    display: inline-flex; align-items: center; gap: 4px; padding: 3px 10px;
    border-radius: 4px; font-size: 11px; font-weight: 700; letter-spacing: 0.04em;
  }
  .tag.warn { color: var(--red); border: 1px solid rgba(196,122,106,0.25); }
  .tag.ok { color: var(--green); border: 1px solid rgba(107,175,122,0.25); }
  .tag.info { color: var(--purple); border: 1px solid rgba(179,136,255,0.25); }
  .tag.dim { color: var(--text-dim); border: 1px solid rgba(139,115,85,0.25); }

  .battle-block {
    padding: 14px; border-radius: var(--radius); background: rgba(10, 8, 5, 0.35);
    border: 1px solid rgba(212, 165, 116, 0.08); font-size: 13px; line-height: 1.7; margin-bottom: 10px;
    backdrop-filter: blur(4px);
  }
  .battle-block .who { font-size: 11px; color: var(--gold); font-weight: 700; margin-bottom: 5px; letter-spacing: 0.06em; }

  .hidden { display: none !important; }
  .dim { color: var(--text-dim); }
  .green { color: var(--green); }
  .red { color: var(--red); }

  /* ── spinner ── */
  .spinner-overlay {
    display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%;
    z-index: 100; pointer-events: none;
    background: radial-gradient(ellipse at center, rgba(15,12,9,0.4) 0%, rgba(15,12,9,0.7) 100%);
  }
  .spinner-overlay.show { display: block; }
  .spinner-box {
    position: fixed; top: 50%; left: 50%;
    transform: translate(-50%, -50%);
    width: 100px; height: 100px; z-index: 101; pointer-events: none;
    display: none;
  }
  .spinner-ring {
    position: absolute; width: 100%; height: 100%;
    border: 3px solid transparent; border-top-color: var(--gold);
    border-radius: 50%; animation: spinnerSpin 1.8s linear infinite;
  }
  .spinner-ring:nth-child(2) {
    width: 70%; height: 70%; top: 15%; left: 15%;
    border-top-color: var(--gold-dim);
    animation-duration: 1.3s; animation-direction: reverse;
  }
  .spinner-ring:nth-child(3) {
    width: 40%; height: 40%; top: 30%; left: 30%;
    border-top-color: var(--gold-light);
    animation-duration: 1s;
  }
  .spinner-label {
    position: absolute; top: 50%; left: 50%;
    transform: translate(-50%, -50%);
    color: var(--gold); font-size: 11px; letter-spacing: 3px;
    animation: spinTextPulse 1.4s ease-in-out infinite;
  }
  @keyframes spinnerSpin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
  @keyframes spinTextPulse { 0%,100% { opacity: 0.4; } 50% { opacity: 1; } }

  .step-dot { transition: all 0.4s ease; }

  @media (max-width: 640px) {
    .form-grid { grid-template-columns: 1fr; }
    .form-grid .wide { grid-column: span 1; }
    .hero-circle { width: 160px; height: 160px; }
    .hero-title { font-size: 22px; letter-spacing: 4px; }
  }
</style>
</head>
<body>
  <!-- decorative background -->
  <div class="deco-bg"><div class="deco-ring"></div><div class="deco-ring"></div><div class="deco-ring"></div></div>
  <div class="ink-layer" id="inkLayer"></div>

  <!-- spinner -->
  <div class="spinner-overlay" id="spinnerOverlay"></div>
  <div class="spinner-box" id="spinnerBox">
    <div class="spinner-ring"></div><div class="spinner-ring"></div><div class="spinner-ring"></div>
    <div class="spinner-label">裁 决 中</div>
  </div>

  <!-- ====== HERO SCREEN (login circle) ====== -->
  <div class="hero-screen" id="heroScreen">
    <div class="hero-circle" id="heroCircle">
      <svg viewBox="0 0 300 300">
        <!-- outer ring -->
        <circle cx="150" cy="150" r="140" fill="none" stroke="#8b7355" stroke-width="1.5" opacity="0.35"/>
        <circle cx="150" cy="150" r="125" fill="none" stroke="#8b7355" stroke-width="0.8" opacity="0.15" stroke-dasharray="4 6"/>
        <!-- inner ring -->
        <circle cx="150" cy="150" r="100" fill="none" stroke="#d4a574" stroke-width="1" opacity="0.2"/>
        <!-- trigram marks -->
        <g stroke="#d4a574" stroke-width="2" opacity="0.3" fill="none">
          <!-- top -->
          <line x1="135" y1="42" x2="165" y2="42"/>
          <line x1="140" y1="48" x2="160" y2="48"/>
          <!-- bottom -->
          <line x1="135" y1="258" x2="165" y2="258"/>
          <line x1="140" y1="252" x2="160" y2="252"/>
          <!-- left -->
          <line x1="42" y1="135" x2="42" y2="165"/>
          <line x1="48" y1="140" x2="48" y2="160"/>
          <!-- right -->
          <line x1="258" y1="135" x2="258" y2="165"/>
          <line x1="252" y1="140" x2="252" y2="160"/>
        </g>
        <!-- center yin-yang dots -->
        <circle cx="150" cy="120" r="18" fill="none" stroke="#d4a574" stroke-width="1.5" opacity="0.3"/>
        <circle cx="150" cy="180" r="18" fill="none" stroke="#d4a574" stroke-width="1.5" opacity="0.3"/>
        <circle cx="132" cy="150" r="18" fill="none" stroke="#d4a574" stroke-width="1.5" opacity="0.3"/>
        <circle cx="168" cy="150" r="18" fill="none" stroke="#d4a574" stroke-width="1.5" opacity="0.3"/>
        <!-- center dot -->
        <circle cx="150" cy="150" r="6" fill="#d4a574" opacity="0.5"/>
        <!-- branch labels -->
        <text x="150" y="22" text-anchor="middle" font-size="10" fill="#d4a574" opacity="0.35">子</text>
        <text x="278" y="153" text-anchor="middle" font-size="10" fill="#d4a574" opacity="0.35">午</text>
        <text x="22" y="153" text-anchor="middle" font-size="10" fill="#d4a574" opacity="0.35">卯</text>
        <text x="150" y="290" text-anchor="middle" font-size="10" fill="#d4a574" opacity="0.35">酉</text>
      </svg>
    </div>

    <div class="hero-title">命理裁决台</div>
    <div class="hero-sub">天机秘册 · 古今相聚</div>
    <div class="hero-hint" id="heroHint">— 轻触八卦 · 开启裁决 —</div>

    <div class="hero-password" id="heroPassword">
      <input id="pwInput" type="password" placeholder="输入密码" />
      <button id="pwSubmit">进入</button>
    </div>
    <div class="hero-err" id="heroErr">密码错误</div>
  </div>

  <!-- ====== MAIN UI ====== -->
  <div class="container" id="mainUI" style="display:none;">

    <div class="header">
      <div class="logo"><em>命理</em>裁决台 <small>· 天机秘册</small></div>
      <div style="display:flex;align-items:center;gap:12px;">
        <span id="statusDot" class="pill idle">待命</span>
        <button id="logoutBtn" class="hidden">退出</button>
      </div>
    </div>

    <div class="card hidden" id="inputCard">
      <div class="card-title">发起分析</div>
      <div style="display:grid;gap:14px;">
        <label>
          你想问什么？
          <textarea id="query" placeholder="请综合分析我未来三年的事业和财运趋势"></textarea>
        </label>
        <div class="form-grid">
          <label>姓名<input id="name" value="Demo" /></label>
          <label>出生日期<input id="birthDate" value="1990-06-12" /></label>
          <label>出生时间<input id="birthTime" value="07:45" /></label>
          <label>出生地点<input id="birthPlace" value="上海" /></label>
          <label>时区<input id="timezone" value="Asia/Shanghai" /></label>
          <label>辩论轮数<input id="maxRounds" type="number" min="1" max="20" value="4" /></label>
        </div>
        <div style="display:flex;gap:8px;">
          <button id="doSessionBtn" class="primary" style="flex:1;">开始分析</button>
          <button id="cancelBtn">取消</button>
        </div>
        <div id="sessionMsg" style="font-size:12px;"></div>
      </div>
    </div>

    <div class="card hidden" id="progressCard">
      <div class="card-title">分析进度</div>
      <div id="progressContent"></div>
    </div>

    <div class="card hidden" id="analyzerCard">
      <div class="card-title">流派分析</div>
      <div id="analyzerContent"></div>
    </div>

    <div class="card hidden" id="reportCard">
      <div class="card-title">分析报告</div>
      <div id="reportContent"></div>
    </div>

    <div class="card hidden" id="issuesCard">
      <div class="card-title">争议裁决</div>
      <div id="issuesContent"></div>
    </div>

  </div>

<script>
  let sid = null;
  let es = null;
  let timer = null;
  let events = [];
  let loggedIn = false;

  function $(id) { return document.getElementById(id); }
  function esc(s) { return String(s??"").replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;"); }
  function ts(v) { try { return new Date(v).toLocaleString("zh-CN",{hour12:false}); } catch(_) { return String(v); } }

  const DISP = { "favor-a":"偏向八字", "favor-b":"偏向紫微", conditional:"条件成立", unresolved:"无法裁决", "mutual-validity":"互有成立" };
  const TERM = { "max-rounds-reached":"达到轮数上限", "stability-stop":"稳定停止", "mutual-convergence":"双方收敛", "model-round-failed":"模型失败", "single-sided-issue":"单边分析" };
  const TAG = { contradiction:"warn", consensus:"ok", tension:"ok", "favor-a":"info", "favor-b":"info", unresolved:"dim", "mutual-validity":"ok" };

  // ── ink particles ──
  function initInkParticles() {
    const layer = $("inkLayer");
    for (let i = 0; i < 20; i++) {
      const dot = document.createElement("div");
      dot.className = "ink-dot";
      const sz = Math.random() * 120 + 40;
      dot.style.width = sz + "px"; dot.style.height = sz + "px";
      dot.style.left = Math.random() * 100 + "%";
      dot.style.top = (Math.random() * 60 + 10) + "%";
      dot.style.background = `rgba(${139+Math.random()*40|0}, ${115+Math.random()*30|0}, ${85+Math.random()*30|0}, 0.06)`;
      dot.style.animationDuration = (Math.random() * 25 + 20) + "s";
      dot.style.animationDelay = Math.random() * 10 + "s";
      layer.appendChild(dot);
    }
  }

  // ── cursor particles ──
  let lastSpark = 0;
  document.addEventListener("mousemove", function(e) {
    const now = Date.now();
    if (now - lastSpark < 30) return;
    lastSpark = now;
    for (var n = 0; n < 2; n++) {
      (function(n) {
        setTimeout(function() {
          const p = document.createElement("div");
          p.className = "cursor-spark";
          p.textContent = ["✦","·","◇"][Math.floor(Math.random()*3)];
          p.style.left = (e.clientX + (n-0.5)*6) + "px";
          p.style.top = (e.clientY + (n-0.5)*6) + "px";
          p.style.color = Math.random() > 0.5 ? "#d4a574" : "#e6b584";
          p.style.fontSize = (Math.random() * 4 + 12) + "px";
          p.style.setProperty("--tx", (Math.random()-0.5)*60 + "px");
          p.style.setProperty("--ty", -(Math.random()*40+10) + "px");
          document.body.appendChild(p);
          setTimeout(function() { p.remove(); }, 800);
        }, n * 30);
      })(n);
    }
  });

  // ── click explosion ──
  function sparkExplosion(cx, cy, n, syms, color) {
    for (var i = 0; i < n; i++) {
      (function(i) {
        setTimeout(function() {
          const p = document.createElement("div");
          p.className = "cursor-spark";
          p.textContent = (syms||["✦","✨"])[Math.floor(Math.random()*(syms||["✦","✨"]).length)];
          p.style.left = cx + "px"; p.style.top = cy + "px";
          p.style.color = color || "#e6b584";
          p.style.fontSize = (Math.random()*4+10) + "px";
          var angle = (i / n) * Math.PI * 2 + Math.random() * 0.3;
          var dist = Math.random() * 50 + 20;
          p.style.setProperty("--tx", Math.cos(angle)*dist + "px");
          p.style.setProperty("--ty", Math.sin(angle)*dist + "px");
          document.body.appendChild(p);
          setTimeout(function() { p.remove(); }, 900);
        }, i * 25);
      })(i);
    }
  }

  // ── brushstroke effect ──
  function brushstroke(cx, cy) {
    for (var i = 0; i < 4; i++) {
      (function(i) {
        setTimeout(function() {
          var angle = (i * 45) * Math.PI / 180;
          var len = 150;
          var x2 = cx + Math.cos(angle) * len;
          var y2 = cy + Math.sin(angle) * len;
          var svg = document.createElementNS("http://www.w3.org/2000/svg","svg");
          svg.setAttribute("width","1000"); svg.setAttribute("height","1000");
          svg.style.cssText = "position:fixed;top:0;left:0;pointer-events:none;z-index:8;";
          var line = document.createElementNS("http://www.w3.org/2000/svg","line");
          line.setAttribute("x1",cx); line.setAttribute("y1",cy);
          line.setAttribute("x2",x2); line.setAttribute("y2",y2);
          line.setAttribute("stroke","#d4a574"); line.setAttribute("stroke-width","1.5");
          line.setAttribute("opacity","0.4");
          line.style.animation = "brushFade 0.8s ease-out forwards";
          svg.appendChild(line);
          document.body.appendChild(svg);
          setTimeout(function(){ svg.remove(); }, 800);
        }, i * 80);
      })(i);
    }
  }
  // inject brushFade keyframes
  (function(){ var s=document.createElement("style"); s.textContent="@keyframes brushFade{0%{opacity:0.5;stroke-dashoffset:200}100%{opacity:0;stroke-dashoffset:0}}"; document.head.appendChild(s); })();

  async function rpc(path, opts) {
    opts = opts||{};
    const r = await fetch(path, { credentials:"include", headers:{"Content-Type":"application/json",...(opts.headers||{})}, ...opts });
    if (!r.ok) {
      const ct = r.headers.get("content-type")||"";
      throw new Error(ct.includes("application/json") ? ((await r.json()).detail||"请求失败") : await r.text());
    }
    const ct = r.headers.get("content-type")||"";
    return ct.includes("application/json") ? r.json() : r.text();
  }

  // ── hero / login ──
  $("heroCircle").addEventListener("click", function(e) {
    // particle explosion
    var rect = this.getBoundingClientRect();
    var cx = rect.left + rect.width/2;
    var cy = rect.top + rect.height/2;
    sparkExplosion(cx, cy, 12, ["卦","象","道","缘","天","地","人","和"], "#d4a574");
    brushstroke(cx, cy);
    // shake circle
    this.style.animation = "none";
    // show password input
    $("heroPassword").classList.add("show");
    $("heroHint").style.display = "none";
    $("pwInput").focus();
  });

  $("pwInput").addEventListener("keydown", function(e) {
    if (e.key === "Enter") doHeroLogin();
  });
  $("pwSubmit").addEventListener("click", doHeroLogin);

  async function doHeroLogin() {
    var pw = $("pwInput").value;
    if (!pw) return;
    try {
      await rpc("/api/login", { method:"POST", body:JSON.stringify({password:pw}) });
      // login success → transition to main UI
      loggedIn = true;
      $("heroErr").style.display = "none";
      $("heroScreen").classList.add("hidden");
      $("mainUI").style.display = "grid";
      $("inputCard").classList.remove("hidden");
      $("logoutBtn").classList.remove("hidden");
      // ensure circle pulse resumes after transition
      setTimeout(function(){ $("heroCircle").style.animation = "heroPulse 4s ease-in-out infinite"; }, 1000);
    } catch(e) {
      $("heroErr").style.display = "block";
      $("pwInput").value = "";
      $("pwInput").focus();
    }
  }

  async function doLogout() {
    await rpc("/api/logout", { method:"POST" });
    if (es) { es.close(); es=null; }
    sid=null; events=[]; loggedIn=false;
    $("mainUI").style.display = "none";
    $("inputCard").classList.add("hidden");
    $("progressCard").classList.add("hidden");
    $("analyzerCard").classList.add("hidden");
    $("reportCard").classList.add("hidden");
    $("issuesCard").classList.add("hidden");
    $("logoutBtn").classList.add("hidden");
    // reset hero
    $("heroScreen").classList.remove("hidden");
    $("heroPassword").classList.remove("show");
    $("heroHint").style.display = "block";
    $("heroErr").style.display = "none";
    $("pwInput").value = "";
  }

  // ── session ──
  async function doSession() {
    const p = {
      query:$("query").value, name:$("name").value||null,
      birth_date:$("birthDate").value||null, birth_time:$("birthTime").value||null,
      birth_place:$("birthPlace").value||null, timezone:$("timezone").value||null,
      max_battle_rounds:Number($("maxRounds").value||4), credential_mode:"server",
      provider_configs:{
        bazi_analyzer:{provider:"openrouter",model:"tencent/hy3-preview:free"},
        ziwei_analyzer:{provider:"openrouter",model:"tencent/hy3-preview:free"},
        bazi_battler:{provider:"openrouter",model:"tencent/hy3-preview:free"},
        ziwei_battler:{provider:"openrouter",model:"tencent/hy3-preview:free"},
        judge:{provider:"openrouter",model:"tencent/hy3-preview:free"},
      },
    };
    showSpinner();
    var spinnerTimer = setTimeout(function(){ hideSpinner(); }, 8000);
    try {
      const r = await rpc("/api/sessions", { method:"POST", body:JSON.stringify(p) });
      hideSpinner();
      $("sessionMsg").innerHTML = '<span class="green">会话已创建：'+r.session_id+'，分析中...</span>';
      attach(r.session_id);
    } catch(e) {
      hideSpinner(); clearTimeout(spinnerTimer);
      throw e;
    }
  }

  async function doCancel() {
    if (!sid) return;
    await rpc("/api/sessions/"+sid+"/cancel", { method:"POST" });
    $("sessionMsg").innerHTML = '<span class="dim">已请求取消</span>';
    hideSpinner();
  }

  function showSpinner() {
    $("spinnerOverlay").classList.add("show");
    $("spinnerBox").style.display = "block";
  }
  function hideSpinner() {
    $("spinnerOverlay").classList.remove("show");
    $("spinnerBox").style.display = "none";
  }

  function pill(s) {
    var cls=s==="running"?"running":s==="completed"?"done":s==="failed"?"failed":"idle";
    var labels={running:"运行中", completed:"已完成", failed:"失败", cancelled:"已取消", idle:"待命"};
    return '<span class="pill '+cls+'">'+(labels[s]||s||"待命")+'</span>';
  }

  function nowStep() {
    if (!events.length) return "等待中";
    var types = events.map(function(e){ return e.event_type; });
    if (types.includes("session_failed")) return "失败";
    if (types.includes("report_ready")||types.includes("session_finished")) return "已完成";
    if (types.includes("judge_completed")) return "裁决中";
    if (types.includes("round_started")||types.includes("round_completed")) return "辩论中";
    if (types.includes("issues_detected")) return "识别争点";
    if (types.includes("analyzer_completed")) return "分析中";
    if (types.includes("chart_resolved")) return "排盘完成";
    return "启动中";
  }

  function renderProgress() {
    var steps=["session_started","chart_resolved","analyzer_completed","issues_detected","round_completed","judge_completed","report_ready"];
    var seen=new Set(events.map(function(e){ return e.event_type; }));
    var labels={session_started:"启动",chart_resolved:"排盘",analyzer_completed:"分析",issues_detected:"争点",round_completed:"辩论",judge_completed:"裁决",report_ready:"报告"};
    var html='<div style="display:flex;gap:16px;flex-wrap:wrap;align-items:center;">';
    for (var i=0;i<steps.length;i++) {
      var s=steps[i];
      var done=seen.has(s)||(s==="analyzer_completed"&&seen.has("analyzer_failed"));
      var active=!done&&(i===0||seen.has(steps[i-1]));
      var c=done?"var(--green)":active?"var(--gold)":"var(--text-dim)";
      html+='<span class="step-dot" style="font-size:12px;color:'+c+';font-weight:'+(active||done?700:400)+';letter-spacing:0.04em;">';
      html+=done?"●":active?"◉":"○"; html+=" "+labels[s]+'</span>';
      if(i<steps.length-1) html+='<span style="color:var(--text-dim);opacity:0.3;">—</span>';
    }
    html+='</div>'; return html;
  }

  function attach(id) {
    sid=id; events=[];
    if(es){es.close();es=null;}
    $("progressCard").classList.remove("hidden");
    $("progressContent").innerHTML='<div style="font-size:13px;color:var(--gold);">连接中...</div>';
    $("reportCard").classList.add("hidden");
    $("issuesCard").classList.add("hidden");
    fetchDetail(id);
    es=new EventSource("/api/sessions/"+id+"/events",{withCredentials:true});
    es.onmessage=function(e){
      var d=JSON.parse(e.data);
      var idx=events.findIndex(function(x){return x.seq===d.seq;});
      if(idx>=0) events[idx]=d; else events.push(d);
      events.sort(function(a,b){return(a.seq||0)-(b.seq||0);});
      liveUpdate(d);
    };
    es.onerror=function(){
      if(timer) clearTimeout(timer);
      timer=setTimeout(function(){if(sid)fetchDetail(sid).then(liveUpdate);},800);
    };
  }

  async function fetchDetail(id) {
    try {
      var d=await rpc("/api/sessions/"+id);
      events=d.events||[];
      $("statusDot").innerHTML=pill(d.status);
      return d;
    }catch(_){return null;}
  }

  function liveUpdate(d) {
    if(!d) return;
    $("statusDot").innerHTML=pill(d.status||"running");
    $("progressContent").innerHTML=renderProgress()+'<div style="margin-top:8px;font-size:11px;color:var(--text-dim);">'+nowStep()+'</div>';
    if(d.events&&d.events.length>0) hideSpinner();
    var s=d.snapshot||{};
    var evidence=s.system_evidence||[];
    if(evidence.length) renderAnalyzerOutput(evidence);
    var issues=s.debate_issues||[];
    var transcript=s.debate_transcript||[];
    if(issues.length||transcript.length) renderIssuesLive(d);
    var report=d.report||s.fusion_report||null;
    if(report) renderReport(d);
    if(["completed","failed","cancelled"].includes(d.status)){$("progressCard").classList.add("hidden");hideSpinner();}
  }

  function renderAnalyzerOutput(evidence) {
    var html='';
    for(var ev of evidence){
      var text=ev.analysis_text||"";
      if(!text) continue;
      var sys=ev.system==="bazi"?"八字":"紫微";
      html+='<div class="battle-block" style="margin-bottom:10px;"><div class="who">'+sys+' 分析结果</div><div style="font-size:13px;line-height:1.8;white-space:pre-wrap;max-height:300px;overflow:auto;">'+esc(text.slice(0,2000))+'</div></div>';
    }
    if(html){$("analyzerCard").classList.remove("hidden");$("analyzerContent").innerHTML=html;}
  }

  function renderIssuesLive(d) {
    var s=d.snapshot||{};
    var issues=s.debate_issues||[];
    var judgements=s.judgements||[];
    var transcript=s.debate_transcript||[];
    if(!issues.length) return;
    $("issuesCard").classList.remove("hidden");
    $("issuesContent").innerHTML=issues.map(function(iss,i){
      var j=judgements.find(function(x){return x.issue_id===iss.issue_id;});
      var r=transcript.filter(function(x){return x.issue_id===iss.issue_id;});
      var cls=TAG[iss.relation]||"dim";
      var dcls=j?TAG[j.disposition]||"dim":"dim";
      var battle=r.length?r.map(function(x,ri){
        var sys=x.system==="bazi"?"八字":"紫微";
        var text=x.public_response||x.response||"";
        return '<div class="battle-block"><div class="who">'+esc(sys)+' · 第'+(x.round_index??ri+1)+'轮</div><div style="font-size:13px;line-height:1.8;white-space:pre-wrap;">'+esc(text)+'</div></div>';
      }).join(""):'<div class="dim" style="font-size:13px;padding:8px 0;">辩论即将开始...</div>';
      return '<div class="issue-item"><div style="padding:12px 16px;background:rgba(212,165,116,0.02);border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between;"><div><strong style="font-size:14px;">'+esc(iss.question||iss.issue_id)+'</strong><div style="font-size:11px;color:var(--text-dim);margin-top:3px;">'+(TERM[iss.termination_reason]||"")+' · '+(iss.rounds_completed??0)+'轮'+(j?" · 已裁决":" · 裁决中...")+'</div></div><div style="display:flex;gap:6px;"><span class="tag '+cls+'">'+(iss.relation||"?")+'</span>'+(j?'<span class="tag '+dcls+'">'+(DISP[j.disposition]||j.disposition)+'</span>':"")+'</div></div><div style="padding:16px;">'+battle+'</div>'+(j?'<div class="issue-item" style="border-radius:0;border-left:0;border-right:0;border-bottom:0;"><div class="issue-head" onclick="this.parentElement.classList.toggle(\'open\')" style="border-top:1px solid var(--border);"><span style="font-size:13px;color:var(--gold);">查看裁决详情</span><span style="font-size:11px;color:var(--text-dim);">'+esc(j.summary||"")+'</span></div><div class="issue-body" style="padding:0 16px 16px;"><div style="font-size:13px;line-height:1.8;">'+esc(j.rationale||"")+'</div>'+(j.conditions&&j.conditions.length?'<div style="margin-top:10px;font-size:12px;color:var(--text-dim);line-height:1.7;">'+j.conditions.map(function(c){return "· "+esc(c);}).join("<br>")+'</div>':"")+'</div></div>':"")+'</div>';
    }).join("");
  }

  function renderReport(d) {
    var r=d.report||(d.snapshot||{}).fusion_report||null;
    if(!r){$("reportCard").classList.add("hidden");return;}
    $("reportCard").classList.remove("hidden");
    var html='<div class="report-text">'+esc(r.summary||"暂无摘要")+'</div>';
    var sections=[["共识",r.consensus_points||[]],["分歧",r.disagreement_points||[]],["保留意见",r.reservations||[]]];
    html+='<div style="display:grid;gap:12px;margin-top:16px;">';
    sections.forEach(function(tuple){
      var t=tuple[0],items=tuple[1];
      html+='<div style="padding:12px;border-radius:var(--radius);background:rgba(10,8,5,0.3);border:1px solid var(--border);backdrop-filter:blur(4px);"><div style="font-size:11px;color:var(--text-dim);letter-spacing:0.06em;margin-bottom:6px;">'+t+'</div>'+(items.length?'<ul style="padding-left:14px;display:grid;gap:3px;">'+items.map(function(i){return '<li style="font-size:13px;line-height:1.6;">'+esc(i)+'</li>';}).join("")+'</ul>':'<div class="dim" style="font-size:12px;">暂无</div>')+'</div>';
    });
    html+='</div>';
    $("reportContent").innerHTML=html;
  }

  // ── events ──
  $("logoutBtn").addEventListener("click", function(){ doLogout().catch(function(){}); });
  $("doSessionBtn").addEventListener("click", function(){ doSession().catch(function(e){ $("sessionMsg").innerHTML='<span class="red">'+esc(e.message)+'</span>'; hideSpinner(); }); });
  $("cancelBtn").addEventListener("click", function(){ doCancel().catch(function(){}); });

  // auto-check existing login
  (async function(){
    try {
      await rpc("/api/sessions");
      loggedIn=true;
      $("heroScreen").classList.add("hidden");
      $("mainUI").style.display="grid";
      $("inputCard").classList.remove("hidden");
      $("logoutBtn").classList.remove("hidden");
    } catch(_) {}
  })();

  initInkParticles();
</script>
</body>
</html>
"""
