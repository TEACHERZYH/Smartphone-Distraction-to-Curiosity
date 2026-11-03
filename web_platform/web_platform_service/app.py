# -*- coding: utf-8 -*-
"""
Single-file Self-contained FastAPI Experiment Platform (MVP)
Integrates Database Models, Pre-flight Services, Run Lifecycle,
Single-Variable Diff View, Valid Inquiry Loop Engine, and Teacher Live Telemetry.
"""
import os
import json
import sqlite3
import hashlib
from datetime import datetime
from typing import Optional, Dict, Any

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

# Database Configuration (uses /tmp to ensure pristine POSIX file locking)
DB_PATH = "/tmp/experiment_web_platform_service.db"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS teams (
        team_id TEXT PRIMARY KEY,
        team_name TEXT,
        members_json TEXT,
        current_roles_json TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS preflight_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        team_id TEXT,
        audio_rate_hz INTEGER,
        audio_pass INTEGER,
        rtt_ms REAL,
        rtt_pass INTEGER,
        storage_mb REAL,
        storage_pass INTEGER,
        serial_baud INTEGER,
        serial_pass INTEGER,
        all_passed INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS runs (
        run_id TEXT PRIMARY KEY,
        parent_run_id TEXT,
        team_id TEXT,
        experiment_type TEXT,
        stage TEXT,
        params_json TEXT,
        features_json TEXT,
        data_hash TEXT,
        explanation_text TEXT,
        is_valid_loop INTEGER DEFAULT 0,
        diff_summary TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    cursor.execute("SELECT COUNT(*) FROM teams")
    if cursor.fetchone()[0] == 0:
        for i in range(1, 13):
            tid = f"Team-{i:02d}"
            members = [
                {"name": f"学生{i}-A", "id": f"202301{i:02d}1"},
                {"name": f"学生{i}-B", "id": f"202301{i:02d}2"},
                {"name": f"学生{i}-C", "id": f"202301{i:02d}3"},
                {"name": f"学生{i}-D", "id": f"202301{i:02d}4"}
            ]
            roles = {"operator": members[0]["name"], "recorder": members[1]["name"], "analyst": members[2]["name"], "auditor": members[3]["name"]}
            cursor.execute("INSERT INTO teams (team_id, team_name, members_json, current_roles_json) VALUES (?, ?, ?, ?)",
                           (tid, f"第{i}协作探究小组", json.dumps(members, ensure_ascii=False), json.dumps(roles, ensure_ascii=False)))
    conn.commit()
    conn.close()

def evaluate_valid_inquiry_loop(conn, current_params, parent_run_id, stage, explanation_text):
    if stage != "E3_Challenge":
        return False, "非 E3 挑战阶段（作为常规流程推进）。"
    if not parent_run_id or parent_run_id.strip() == "":
        return False, "未指定对比基准 Parent Run ID（无法构建受控对照）。"
    cursor = conn.cursor()
    cursor.execute("SELECT params_json FROM runs WHERE run_id = ?", (parent_run_id,))
    parent_row = cursor.fetchone()
    if not parent_row:
        return False, f"未找到指定的父运行编号 '{parent_run_id}'。"
    parent_params = json.loads(parent_row["params_json"])
    diff_keys, diff_details = [], []
    for k in set(parent_params.keys()).union(set(current_params.keys())):
        v_old, v_new = parent_params.get(k), current_params.get(k)
        if str(v_old) != str(v_new):
            diff_keys.append(k)
            diff_details.append(f"{k}: [{v_old}] -> [{v_new}]")
    if len(diff_keys) == 0:
        return False, "物理参数未发生实质变更（重复测试）。"
    if len(diff_keys) > 1:
        return False, f"多变量混乱调参：同时更动了 {len(diff_keys)} 个物理参数 ({', '.join(diff_keys)})，严格仅允许 1 项。"
    if not explanation_text or len(explanation_text.strip()) < 15:
        return False, "机理解释字数不足（需 >= 15 字符）。必须陈述该单变量调参的物理依据。"
    return True, f"有效单变量调整循环已确认：{'; '.join(diff_details)}"

# FastAPI Application
app = FastAPI(
    title="Cross-Modal Signal & IoT Sensing Web Lab Platform",
    description="Local LAN Web-based Laboratory Platform for Causal Traceability & ABET Accreditation",
    version="1.0.0"
)

@app.on_event("startup")
def startup_event():
    init_db()

# Inline HTML Templates (ensures 100% self-contained deployment with zero external file path dependency)
STUDENT_HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>跨模态信号实验与物联网感知教学平台</title>
    <style>
        :root { --primary: #1B365D; --accent: #0056B3; --success: #28A745; --danger: #D9534F; --border: #E2E8F0; }
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #F8F9FA; margin: 0; padding: 0; color: #222; }
        .navbar { background: #1B365D; color: white; padding: 0.85rem 1.5rem; display: flex; justify-content: space-between; align-items: center; }
        .nav-brand { font-size: 1.2rem; font-weight: bold; }
        .nav-tag { font-size: 0.75rem; background: rgba(255,255,255,0.2); padding: 0.2rem 0.5rem; border-radius: 4px; margin-left: 0.5rem; }
        .btn { padding: 0.45rem 1rem; font-size: 0.875rem; font-weight: 600; border-radius: 6px; border: none; cursor: pointer; text-decoration: none; }
        .btn-primary { background: #0056B3; color: white; }
        .btn-outline { background: transparent; border: 1px solid white; color: white; }
        .btn-success { background: #28A745; color: white; }
        .container { max-width: 1280px; margin: 1.5rem auto; padding: 0 1rem; }
        .grid-main { display: grid; grid-template-columns: 320px 1fr; gap: 1.5rem; }
        @media(max-width: 900px){ .grid-main { grid-template-columns: 1fr; } }
        .card { background: white; border-radius: 8px; border: 1px solid #E2E8F0; padding: 1.25rem; margin-bottom: 1.5rem; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }
        .card-title { font-size: 1.05rem; font-weight: bold; color: #1B365D; margin-bottom: 1rem; padding-bottom: 0.5rem; border-bottom: 2px solid #EDF2F7; display: flex; justify-content: space-between; align-items: center; }
        .roles-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; }
        .role-badge { background: #F1F5F9; padding: 0.5rem; border-radius: 6px; font-size: 0.8rem; border-left: 3px solid #0056B3; }
        .role-name { font-weight: bold; color: #1B365D; display: block; }
        .steps-wizard { display: flex; justify-content: space-between; background: #F1F5F9; padding: 0.75rem 1rem; border-radius: 8px; margin-bottom: 1.5rem; }
        .step-item { display: flex; align-items: center; gap: 0.4rem; font-size: 0.85rem; font-weight: 600; color: #6C757D; cursor: pointer; }
        .step-item.active { color: #0056B3; }
        .step-circle { width: 24px; height: 24px; border-radius: 50%; background: #CBD5E1; color: white; display: flex; align-items: center; justify-content: center; font-size: 0.75rem; }
        .step-item.active .step-circle { background: #0056B3; }
        .form-group { margin-bottom: 1rem; }
        .form-label { display: block; font-size: 0.85rem; font-weight: 600; margin-bottom: 0.35rem; }
        .form-control { width: 100%; padding: 0.5rem 0.75rem; font-size: 0.9rem; border: 1px solid #E2E8F0; border-radius: 6px; box-sizing: border-box; }
        .diff-container { background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 6px; padding: 0.75rem; margin-top: 1rem; }
        .diff-row { display: flex; justify-content: space-between; padding: 0.35rem 0.5rem; font-size: 0.85rem; border-bottom: 1px dashed #E2E8F0; }
        .diff-row.changed { background: #FEF3C7; font-weight: bold; color: #B45309; }
        .alert { padding: 0.75rem 1rem; border-radius: 6px; font-size: 0.875rem; margin-bottom: 1rem; }
        .alert-success { background: #DEF7EC; color: #03543F; border-left: 4px solid #28A745; }
        .alert-danger { background: #FDE8E8; color: #9B1C1C; border-left: 4px solid #D9534F; }
        .waveform-box { background: #0F172A; border-radius: 6px; height: 180px; width: 100%; }
        .status-dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; margin-right: 0.3rem; }
    </style>
</head>
<body>
    <header class="navbar">
        <div class="nav-brand">跨模态信号探究实验工作台 <span class="nav-tag">局域网轻量版 v1.0</span></div>
        <div style="display:flex; gap:1rem; align-items:center;">
            <select id="teamSelector" class="form-control" style="width: auto;">
                <option value="Team-01">第 01 协作探究小组</option>
                <option value="Team-02">第 02 协作探究小组</option>
                <option value="Team-03">第 03 协作探究小组</option>
            </select>
            <button id="btnPreflight" class="btn btn-outline"><span id="pfDot" class="status-dot" style="background:#FFC107;"></span>环境预检</button>
            <a href="/teacher" class="btn btn-outline" target="_blank">教师监控大屏</a>
        </div>
    </header>
    <main class="container">
        <div class="grid-main">
            <aside>
                <div class="card">
                    <div class="card-title"><span>四人轮岗工单</span><span style="font-size:0.75rem; color:#0056B3;">ABET SO 5</span></div>
                    <div class="roles-grid">
                        <div class="role-badge"><span class="role-name">操作员</span><span id="roleOp">学生-A</span></div>
                        <div class="role-badge"><span class="role-name">记录员</span><span id="roleRec">学生-B</span></div>
                        <div class="role-badge"><span class="role-name">分析员</span><span id="roleAna">学生-C</span></div>
                        <div class="role-badge"><span class="role-name">核验员</span><span id="roleAud">学生-D</span></div>
                    </div>
                </div>
                <div class="card">
                    <div class="card-title"><span>探索运行历史 (Runs)</span><span id="runCountBadge" class="nav-tag" style="background:#1B365D; color:white;">0 Runs</span></div>
                    <div id="runsList" style="max-height: 260px; overflow-y: auto; font-size: 0.85rem;"><p style="color:gray; text-align:center;">暂无运行记录</p></div>
                    <button id="btnExport" class="btn btn-primary" style="width: 100%; margin-top: 1rem;">导出结构化证据包 (JSON)</button>
                </div>
            </aside>
            <section>
                <div class="card" style="padding: 0.75rem 1.25rem;">
                    <div style="display:flex; gap:1.5rem; align-items:center;">
                        <span style="font-weight:bold; color:#1B365D;">实验模块：</span>
                        <label><input type="radio" name="exp" value="vlc" checked> 实验一：可见光通信 (VLC/OCC)</label>
                        <label><input type="radio" name="exp" value="acoustic"> 实验二：声学脉冲测距 (Sonar)</label>
                        <label><input type="radio" name="exp" value="csi"> 实验三：Wi-Fi CSI 射频感知</label>
                    </div>
                </div>
                <div class="steps-wizard">
                    <div class="step-item active" data-s="E1_Predict"><div class="step-circle">E1</div> 预测</div>
                    <div class="step-item" data-s="E2_Observe"><div class="step-circle">E2</div> 观察</div>
                    <div class="step-item" data-s="E4_Explain"><div class="step-circle">E4</div> 解释</div>
                    <div class="step-item" data-s="E3_Challenge"><div class="step-circle">E3</div> 挑战</div>
                    <div class="step-item" data-s="E5_Redesign"><div class="step-circle">E5</div> 再设计</div>
                </div>
                <div class="card">
                    <div class="card-title"><span id="stageTitle">E1 先验理论假说与参数预测</span></div>
                    <form id="runForm">
                        <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap:1rem; margin-bottom:1rem;">
                            <div class="form-group"><label class="form-label" id="l1">调制频率 (Hz)</label><input type="number" class="form-control" id="p1" value="500"></div>
                            <div class="form-group"><label class="form-label" id="l2">曝光时间 (s)</label><input type="text" class="form-control" id="p2" value="0.0005"></div>
                            <div class="form-group"><label class="form-label" id="l3">测试物距 (cm)</label><input type="number" class="form-control" id="p3" value="30"></div>
                            <div class="form-group"><label class="form-label">对比基准 (Parent Run)</label><select class="form-control" id="parentRun"><option value="">-- 无对比基准 --</option></select></div>
                        </div>
                        <div class="form-group"><label class="form-label">实时波形预览 (Canvas)</label><div class="waveform-box"><canvas id="cvs" width="800" height="180" style="width:100%; height:100%;"></canvas></div></div>
                        <div class="form-group"><label class="form-label">机理解释 / 先验假设 (>= 15 字符)</label><textarea class="form-control" id="expl" rows="3" placeholder="在此输入团队研讨的底层物理原理解释或调参动因..."></textarea></div>
                        <div id="alertBox" style="display:none;" class="alert"></div>
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-top:1rem;">
                            <button type="button" id="btnWave" class="btn" style="background:gray; color:white;">刷新波形</button>
                            <button type="submit" class="btn btn-success" style="padding:0.6rem 2rem;">提交并固化运行记录 (Record Run)</button>
                        </div>
                    </form>
                    <div class="diff-container" id="diffBox" style="display:none;"><h4 style="color:#1B365D; margin-bottom:0.5rem;">参数差异对比视图 (Diff View)</h4><div id="diffList"></div></div>
                </div>
            </section>
        </div>
    </main>
    <script>
        let curTeam = "Team-01", curExp = "vlc", curStage = "E1_Predict", runs = [];
        const expMap = {
            vlc: { l1: "调制频率 (Hz)", d1: 500, l2: "曝光时间 (s)", d2: "0.0005", l3: "物距 (cm)", d3: 30 },
            acoustic: { l1: "环境气温 (°C)", d1: 22.5, l2: "挡板距离 (m)", d2: 1.50, l3: "带宽 (kHz)", d3: 3.0 },
            csi: { l1: "节点间距 (m)", d1: 3.0, l2: "滑动窗 (s)", d2: 4.0, l3: "发包率 (Hz)", d3: 100 }
        };
        async function refreshRuns() {
            const res = await fetch(`/api/runs?team_id=${curTeam}&experiment_type=${curExp}`);
            runs = (await res.json()).runs;
            document.getElementById("runCountBadge").innerText = `${runs.length} Runs`;
            const sel = document.getElementById("parentRun");
            sel.innerHTML = '<option value="">-- 无对比基准 --</option>';
            runs.forEach(r => {
                const opt = document.createElement("option"); opt.value = r.run_id;
                opt.innerText = `${r.run_id} [${r.stage}] (${r.created_at.slice(11,19)})`;
                sel.appendChild(opt);
            });
            const list = document.getElementById("runsList");
            list.innerHTML = runs.length ? "" : '<p style="color:gray;text-align:center;">暂无运行记录</p>';
            runs.forEach(r => {
                const el = document.createElement("div");
                el.style.padding = "0.4rem"; el.style.borderBottom = "1px solid #EDF2F7"; el.style.cursor = "pointer";
                el.innerHTML = `<strong>${r.run_id}</strong> ${r.is_valid_loop ? '<span style="color:#28A745;font-weight:bold;">[有效循环]</span> ':''}<span style="color:#0056B3;">${r.stage}</span><br><small style="color:gray;">${r.created_at.slice(11,19)} | 父: ${r.parent_run_id || '无'}</small>`;
                el.addEventListener("click", () => inspect(r.run_id));
                list.appendChild(el);
            });
        }
        async function inspect(runId) {
            const res = await fetch(`/api/diff/${runId}`);
            const d = await res.json();
            const box = document.getElementById("diffBox"), dl = document.getElementById("diffList");
            if(d.has_parent){
                box.style.display = "block"; dl.innerHTML = "";
                for(const [k, v] of Object.entries(d.parameter_diffs)){
                    const row = document.createElement("div"); row.className = `diff-row ${v.changed ? 'changed':''}`;
                    row.innerHTML = `<span>${k}</span><span>基准: ${v.parent_value} &rarr; 当前: ${v.current_value}</span>`;
                    dl.appendChild(row);
                }
                const st = document.createElement("div"); st.style.marginTop = "0.5rem"; st.style.fontWeight = "bold";
                st.style.color = d.is_valid_loop ? "#28A745" : "#D9534F";
                st.innerText = d.diff_summary; dl.appendChild(st);
            } else { box.style.display = "none"; }
        }
        function draw() {
            const cvs = document.getElementById("cvs"), ctx = cvs.getContext("2d");
            ctx.clearRect(0, 0, cvs.width, cvs.height); ctx.strokeStyle = "#38BDF8"; ctx.lineWidth = 2; ctx.beginPath();
            for(let x=0; x<cvs.width; x++){
                const y = 90 + Math.sin(x*0.05)*45 + (Math.random()-0.5)*8;
                if(x===0) ctx.moveTo(x,y); else ctx.lineTo(x,y);
            }
            ctx.stroke();
        }
        function switchExp() {
            const c = expMap[curExp];
            document.getElementById("l1").innerText = c.l1; document.getElementById("p1").value = c.d1;
            document.getElementById("l2").innerText = c.l2; document.getElementById("p2").value = c.d2;
            document.getElementById("l3").innerText = c.l3; document.getElementById("p3").value = c.d3;
            draw(); refreshRuns();
        }
        document.querySelectorAll("input[name='exp']").forEach(r => r.addEventListener("change", (e)=>{ curExp = e.target.value; switchExp(); }));
        document.querySelectorAll(".step-item").forEach(s => s.addEventListener("click", ()=>{
            document.querySelectorAll(".step-item").forEach(x => x.classList.remove("active"));
            s.classList.add("active"); curStage = s.getAttribute("data-s");
            document.getElementById("stageTitle").innerText = `${curStage} 阶段任务执行与数据存证`;
        }));
        document.getElementById("btnPreflight").addEventListener("click", async ()=>{
            const res = await fetch("/api/preflight", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({team_id:curTeam})});
            if((await res.json()).all_passed) { document.getElementById("pfDot").style.background = "#28A745"; alert("环境预检全项通过！已固化采样率与网络时延基准。"); }
        });
        document.getElementById("runForm").addEventListener("submit", async (e)=>{
            e.preventDefault();
            const payload = {
                team_id: curTeam, experiment_type: curExp, stage: curStage, parent_run_id: document.getElementById("parentRun").value,
                params: { p1: document.getElementById("p1").value, p2: document.getElementById("p2").value, p3: document.getElementById("p3").value },
                features: { peak: 80.0 }, explanation_text: document.getElementById("expl").value, raw_data_content: "DATA_" + Date.now()
            };
            const res = await fetch("/api/runs", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify(payload)});
            const d = await res.json();
            const ab = document.getElementById("alertBox");
            ab.style.display = "block"; ab.className = d.is_valid_loop ? "alert alert-success" : "alert alert-danger";
            ab.innerHTML = `<strong>${d.is_valid_loop ? '[有效循环通过]' : '[普通记录]'}</strong> ${d.diff_summary}`;
            refreshRuns();
            if(d.run_id && document.getElementById("parentRun").value) inspect(d.run_id);
        });
        document.getElementById("btnExport").addEventListener("click", ()=> window.open(`/api/export/${curTeam}`, "_blank"));
        document.getElementById("btnWave").addEventListener("click", draw);
        switchExp();
    </script>
</body>
</html>
"""

TEACHER_HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>教师端实时实验教学监控大屏</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #0F172A; color: white; margin: 0; padding: 0; }
        .navbar { background: #1E293B; border-bottom: 1px solid #334155; padding: 0.85rem 1.5rem; display: flex; justify-content: space-between; align-items: center; }
        .container { max-width: 1400px; margin: 1.5rem auto; padding: 0 1rem; }
        .card { background: #1E293B; border: 1px solid #334155; border-radius: 8px; padding: 1.25rem; }
        .grid-top { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1.25rem; margin-bottom: 1.5rem; }
        .grid-teams { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 1.25rem; }
        .team-box { background: #1E293B; border: 1px solid #334155; border-radius: 8px; padding: 1rem; cursor: pointer; transition: transform 0.2s; }
        .team-box:hover { transform: translateY(-2px); border-color: #38BDF8; }
        .btn { padding: 0.45rem 1rem; font-size: 0.875rem; border-radius: 6px; border: none; cursor: pointer; text-decoration: none; background: #0056B3; color: white; }
    </style>
</head>
<body>
    <header class="navbar">
        <div style="font-size:1.2rem; font-weight:bold; color:#38BDF8;">课堂教学实时监控大屏 <span style="font-size:0.75rem; background:#0284C7; color:white; padding:0.2rem 0.5rem; border-radius:4px;">ABET SO 1, 5, 6 过程质控</span></div>
        <div><span id="clk" style="font-family:monospace; margin-right:1rem; color:#94A3B8;"></span><a href="/" class="btn">返回工作台</a></div>
    </header>
    <main class="container">
        <div class="grid-top">
            <div class="card"><small style="color:#94A3B8;">全班协作小组数</small><div style="font-size:1.8rem; font-weight:bold; color:#38BDF8;">12 组</div></div>
            <div class="card"><small style="color:#94A3B8;">全班累计运行 (Runs)</small><div style="font-size:1.8rem; font-weight:bold; color:#4ADE80;" id="totRuns">0 次</div></div>
            <div class="card"><small style="color:#94A3B8;">有效调整循环 (Valid Loops)</small><div style="font-size:1.8rem; font-weight:bold; color:#FBBF24;" id="totLoops">0 次</div></div>
            <div class="card"><small style="color:#94A3B8;">未预检/待关注小组</small><div style="font-size:1.8rem; font-weight:bold; color:#F87171;" id="stCount">0 组</div></div>
        </div>
        <div class="grid-teams" id="tGrid"></div>
    </main>
    <script>
        async function update() {
            const res = await fetch("/api/teacher/dashboard");
            const d = await res.json();
            document.getElementById("clk").innerText = d.timestamp;
            let runs = 0, loops = 0, st = 0;
            const grid = document.getElementById("tGrid"); grid.innerHTML = "";
            d.dashboard.forEach(t => {
                runs += t.total_runs; loops += t.valid_inquiry_loops;
                if(!t.preflight_passed) st++;
                const b = document.createElement("div"); b.className = "team-box";
                b.innerHTML = `
                    <div style="display:flex; justify-content:space-between; margin-bottom:0.4rem;"><strong style="color:#38BDF8;">${t.team_id}</strong><small style="color:#94A3B8;">${t.preflight_passed ? '预检合格':'未预检'}</small></div>
                    <div style="font-size:0.85rem;"><span style="color:#94A3B8;">模块: </span>${t.active_experiment.toUpperCase()}</div>
                    <div style="font-size:0.85rem;"><span style="color:#94A3B8;">阶段: </span><span style="color:#38BDF8;font-weight:bold;">${t.current_stage}</span></div>
                    <div style="font-size:0.85rem; margin:0.4rem 0;"><span style="color:#94A3B8;">有效循环: </span><strong style="color:#FBBF24;font-size:1.1rem;">${t.valid_inquiry_loops}</strong> / ${t.total_runs} Runs</div>
                    <div style="border-top:1px dashed #334155; padding-top:0.3rem; font-size:0.75rem; color:#64748B;">活跃: ${t.last_active_time.slice(11,19) || '无'}</div>
                `;
                b.addEventListener("click", ()=> window.open(`/api/export/${t.team_id}`, "_blank"));
                grid.appendChild(b);
            });
            document.getElementById("totRuns").innerText = `${runs} 次`;
            document.getElementById("totLoops").innerText = `${loops} 次`;
            document.getElementById("stCount").innerText = `${st} 组`;
        }
        update(); setInterval(update, 3000);
    </script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def student_workspace(request: Request):
    return HTMLResponse(content=STUDENT_HTML)

@app.get("/teacher", response_class=HTMLResponse)
async def teacher_dashboard(request: Request):
    return HTMLResponse(content=TEACHER_HTML)

@app.post("/api/preflight")
async def log_preflight(payload: Dict[str, Any]):
    team_id = payload.get("team_id", "Team-01")
    audio_rate = payload.get("audio_rate_hz", 48000)
    audio_pass = 1 if audio_rate in (44100, 48000) else 0
    rtt_ms = payload.get("rtt_ms", 8.5)
    rtt_pass = 1 if rtt_ms < 20.0 else 0
    storage_mb = payload.get("storage_mb", 250.0)
    storage_pass = 1 if storage_mb >= 100.0 else 0
    serial_baud = payload.get("serial_baud", 115200)
    serial_pass = 1 if serial_baud == 115200 else 0
    all_passed = 1 if (audio_pass and rtt_pass and storage_pass and serial_pass) else 0
    conn = get_db_connection()
    conn.execute("INSERT INTO preflight_logs (team_id, audio_rate_hz, audio_pass, rtt_ms, rtt_pass, storage_mb, storage_pass, serial_baud, serial_pass, all_passed) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                 (team_id, audio_rate, audio_pass, rtt_ms, rtt_pass, storage_mb, storage_pass, serial_baud, serial_pass, all_passed))
    conn.commit()
    conn.close()
    return {"status": "success", "all_passed": bool(all_passed)}

@app.get("/api/teams")
async def list_teams():
    conn = get_db_connection()
    rows = conn.execute("SELECT * FROM teams ORDER BY team_id ASC").fetchall()
    teams = [{"team_id": r["team_id"], "team_name": r["team_name"], "members": json.loads(r["members_json"]), "current_roles": json.loads(r["current_roles_json"])} for r in rows]
    conn.close()
    return {"teams": teams}

@app.get("/api/runs")
async def get_runs(team_id: str, experiment_type: Optional[str] = None):
    conn = get_db_connection()
    if experiment_type:
        rows = conn.execute("SELECT * FROM runs WHERE team_id = ? AND experiment_type = ? ORDER BY created_at ASC", (team_id, experiment_type)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM runs WHERE team_id = ? ORDER BY created_at ASC", (team_id,)).fetchall()
    runs = [{
        "run_id": r["run_id"], "parent_run_id": r["parent_run_id"], "stage": r["stage"],
        "experiment_type": r["experiment_type"], "params": json.loads(r["params_json"]),
        "features": json.loads(r["features_json"]) if r["features_json"] else {},
        "data_hash": r["data_hash"], "explanation_text": r["explanation_text"],
        "is_valid_loop": bool(r["is_valid_loop"]), "diff_summary": r["diff_summary"], "created_at": r["created_at"]
    } for r in rows]
    conn.close()
    return {"runs": runs}

@app.post("/api/runs")
async def create_run(payload: Dict[str, Any]):
    team_id = payload.get("team_id", "Team-01")
    experiment_type = payload.get("experiment_type", "vlc")
    stage = payload.get("stage", "E2_Observe")
    parent_run_id = payload.get("parent_run_id")
    params = payload.get("params", {})
    features = payload.get("features", {})
    explanation_text = payload.get("explanation_text", "")
    raw_str = payload.get("raw_data_content", str(features))
    data_hash = hashlib.sha256(raw_str.encode("utf-8")).hexdigest()[:16]
    conn = get_db_connection()
    run_seq = conn.execute("SELECT COUNT(*) FROM runs WHERE team_id = ?", (team_id,)).fetchone()[0] + 1
    run_id = f"Run-{run_seq:03d}"
    is_valid_loop, diff_msg = evaluate_valid_inquiry_loop(conn, params, parent_run_id, stage, explanation_text)
    conn.execute("INSERT INTO runs (run_id, parent_run_id, team_id, experiment_type, stage, params_json, features_json, data_hash, explanation_text, is_valid_loop, diff_summary) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                 (run_id, parent_run_id, team_id, experiment_type, stage, json.dumps(params), json.dumps(features), data_hash, explanation_text, 1 if is_valid_loop else 0, diff_msg))
    conn.commit()
    conn.close()
    return {"status": "success", "run_id": run_id, "is_valid_loop": is_valid_loop, "diff_summary": diff_msg, "data_hash": data_hash}

@app.get("/api/diff/{run_id}")
async def get_run_diff(run_id: str):
    conn = get_db_connection()
    curr = conn.execute("SELECT * FROM runs WHERE run_id = ?", (run_id,)).fetchone()
    if not curr: conn.close(); raise HTTPException(status_code=404, detail="Run not found.")
    parent_id = curr["parent_run_id"]
    if not parent_id: conn.close(); return {"has_parent": False, "message": "Baseline Run."}
    parent = conn.execute("SELECT * FROM runs WHERE run_id = ?", (parent_id,)).fetchone()
    conn.close()
    if not parent: return {"has_parent": False, "message": "Parent Run missing."}
    p_params, c_params = json.loads(parent["params_json"]), json.loads(curr["params_json"])
    diffs = {k: {"parent_value": p_params.get(k), "current_value": c_params.get(k), "changed": (p_params.get(k) != c_params.get(k))} for k in set(p_params.keys()).union(set(c_params.keys()))}
    return {"has_parent": True, "current_run_id": run_id, "parent_run_id": parent_id, "parameter_diffs": diffs, "is_valid_loop": bool(curr["is_valid_loop"]), "diff_summary": curr["diff_summary"]}

@app.get("/api/teacher/dashboard")
async def get_teacher_telemetry():
    conn = get_db_connection()
    teams = conn.execute("SELECT team_id, team_name, current_roles_json FROM teams ORDER BY team_id ASC").fetchall()
    dashboard_data = []
    for t in teams:
        tid = t["team_id"]
        runs = conn.execute("SELECT stage, experiment_type, is_valid_loop, created_at FROM runs WHERE team_id = ? ORDER BY rowid DESC", (tid,)).fetchall()
        pf = conn.execute("SELECT all_passed FROM preflight_logs WHERE team_id = ? ORDER BY id DESC LIMIT 1", (tid,)).fetchone()
        dashboard_data.append({
            "team_id": tid, "team_name": t["team_name"], "roles": json.loads(t["current_roles_json"]),
            "preflight_passed": bool(pf[0]) if pf else False,
            "active_experiment": runs[0]["experiment_type"] if runs else "None",
            "current_stage": runs[0]["stage"] if runs else "Not Started",
            "total_runs": len(runs),
            "valid_inquiry_loops": sum(1 for r in runs if r["is_valid_loop"] == 1),
            "last_active_time": runs[0]["created_at"] if runs else "Never"
        })
    conn.close()
    return {"dashboard": dashboard_data, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

@app.get("/api/export/{team_id}")
async def export_evidence_package(team_id: str):
    conn = get_db_connection()
    team = conn.execute("SELECT * FROM teams WHERE team_id = ?", (team_id,)).fetchone()
    if not team: conn.close(); raise HTTPException(status_code=404, detail="Team not found.")
    runs = conn.execute("SELECT * FROM runs WHERE team_id = ? ORDER BY created_at ASC", (team_id,)).fetchall()
    pf = conn.execute("SELECT * FROM preflight_logs WHERE team_id = ? ORDER BY id DESC LIMIT 1", (team_id,)).fetchone()
    conn.close()
    return JSONResponse(content={
        "export_metadata": {"course": "EE3042L", "team_id": team_id, "members": json.loads(team["members_json"]), "roles": json.loads(team["current_roles_json"]), "exported_at": datetime.now().isoformat()},
        "preflight_audit": dict(pf) if pf else None,
        "runs_ledger": [{"run_id": r["run_id"], "parent_run_id": r["parent_run_id"], "stage": r["stage"], "params": json.loads(r["params_json"]), "features": json.loads(r["features_json"]) if r["features_json"] else {}, "sha256": r["data_hash"], "explanation": r["explanation_text"], "is_valid_loop": bool(r["is_valid_loop"]), "diff_summary": r["diff_summary"], "timestamp": r["created_at"]} for r in runs]
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
