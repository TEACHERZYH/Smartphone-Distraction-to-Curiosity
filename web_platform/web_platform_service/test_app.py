# -*- coding: utf-8 -*-
"""
Automated Test Suite for Cross-Modal Signal Experiment Web Platform MVP
Covers:
1. System Health & UI Endpoint Rendering
2. Team Management & ABET SO 5 Role Binding
3. Pre-flight Environment Baseline Checks (Audio, Network RTT, Storage, Serial)
4. Run Record Lifecycle & SHA-256 Data Hash Immutability
5. Diff View & Valid Inquiry Loop Engine (Single-variable validation, multi-variable rejection, explanation length check)
6. Teacher Real-time Telemetry Dashboard & Aggregation
7. ABET Accreditation Evidence Package Structured Export
"""
import sys
import os
import unittest
from fastapi.testclient import TestClient

# Ensure local directory is in path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

import app as web_app

class TestWebPlatformService(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Reset DB for test isolation
        conn = web_app.get_db_connection()
        conn.execute("DROP TABLE IF EXISTS preflight_logs")
        conn.execute("DROP TABLE IF EXISTS runs")
        conn.execute("DROP TABLE IF EXISTS teams")
        conn.commit()
        conn.close()
        web_app.init_db()
        cls.client = TestClient(web_app.app)

    def test_01_ui_endpoints(self):
        """Test Student Workspace and Teacher Dashboard HTML endpoints."""
        resp_student = self.client.get("/")
        self.assertEqual(resp_student.status_code, 200)
        self.assertIn("跨模态信号探究实验工作台", resp_student.text)
        self.assertIn("Canvas", resp_student.text)

        resp_teacher = self.client.get("/teacher")
        self.assertEqual(resp_teacher.status_code, 200)
        self.assertIn("教师端实时实验教学监控大屏", resp_teacher.text)
        self.assertIn("ABET SO 1, 5, 6", resp_teacher.text)

    def test_02_team_management(self):
        """Test team listing and default 12 collaborative groups."""
        resp = self.client.get("/api/teams")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("teams", data)
        self.assertEqual(len(data["teams"]), 12)
        team_01 = data["teams"][0]
        self.assertEqual(team_01["team_id"], "Team-01")
        self.assertIn("members", team_01)
        self.assertEqual(len(team_01["members"]), 4)
        self.assertEqual(team_01["current_roles"]["operator"], "学生1-A")
        self.assertEqual(team_01["current_roles"]["auditor"], "学生1-D")

    def test_03_preflight_check(self):
        """Test pre-flight environment baseline audit."""
        # Test passed pre-flight
        payload_pass = {
            "team_id": "Team-01",
            "audio_rate_hz": 48000,
            "rtt_ms": 6.8,
            "storage_mb": 512.0,
            "serial_baud": 115200
        }
        resp = self.client.post("/api/preflight", json=payload_pass)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "success")
        self.assertTrue(resp.json()["all_passed"])

        # Test failed pre-flight (high latency)
        payload_fail = {
            "team_id": "Team-02",
            "audio_rate_hz": 44100,
            "rtt_ms": 35.4, # > 20ms threshold
            "storage_mb": 512.0,
            "serial_baud": 115200
        }
        resp_fail = self.client.post("/api/preflight", json=payload_fail)
        self.assertEqual(resp_fail.status_code, 200)
        self.assertFalse(resp_fail.json()["all_passed"])

    def test_04_run_lifecycle_and_hash(self):
        """Test recording runs and SHA-256 data hash immutability."""
        payload = {
            "team_id": "Team-01",
            "experiment_type": "vlc",
            "stage": "E1_Predict",
            "params": {"freq_hz": 500, "exposure_s": "0.0005", "dist_cm": 30},
            "features": {"fsk_demod_snr": 18.5, "ber": 0.0},
            "explanation_text": "在500Hz载波下，卷帘快门每行曝光时间足以采样完整明暗条纹周期。",
            "raw_data_content": "VLC_RAW_SAMPLES_TIMESTAMP_20261030_RUN001"
        }
        resp = self.client.post("/api/runs", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("Run-", data["run_id"])
        self.assertEqual(len(data["data_hash"]), 16) # Truncated SHA-256

        # Verify query runs
        resp_list = self.client.get("/api/runs?team_id=Team-01&experiment_type=vlc")
        self.assertEqual(resp_list.status_code, 200)
        runs = resp_list.json()["runs"]
        self.assertGreaterEqual(len(runs), 1)
        self.assertEqual(runs[-1]["data_hash"], data["data_hash"])

    def test_05_valid_inquiry_loop_and_diff(self):
        """
        Test Controlled Experiment Validation Engine (Valid Inquiry Loop):
        1. Baseline Run
        2. Invalid Run (multi-variable change in E3 Challenge)
        3. Invalid Run (no explanation in E3 Challenge)
        4. Valid Run (single-variable change with physical mechanism explanation)
        """
        # Query current runs to get Parent Run ID
        resp_list = self.client.get("/api/runs?team_id=Team-01&experiment_type=vlc")
        parent_id = resp_list.json()["runs"][0]["run_id"]

        # Multi-variable change (freq + exposure) -> Rejected
        bad_payload_multivar = {
            "team_id": "Team-01",
            "experiment_type": "vlc",
            "stage": "E3_Challenge",
            "parent_run_id": parent_id,
            "params": {"freq_hz": 1000, "exposure_s": "0.0002", "dist_cm": 30},
            "features": {"fsk_demod_snr": 12.0},
            "explanation_text": "尝试同时提高频率并压低曝光时间以改善条纹锐利度。",
            "raw_data_content": "VLC_RAW_RUN_002"
        }
        resp_bad = self.client.post("/api/runs", json=bad_payload_multivar)
        self.assertEqual(resp_bad.status_code, 200)
        self.assertFalse(resp_bad.json()["is_valid_loop"])
        self.assertIn("多变量混乱调参", resp_bad.json()["diff_summary"])

        # Single variable but explanation too short (< 15 chars) -> Rejected
        bad_payload_short_expl = {
            "team_id": "Team-01",
            "experiment_type": "vlc",
            "stage": "E3_Challenge",
            "parent_run_id": parent_id,
            "params": {"freq_hz": 800, "exposure_s": "0.0005", "dist_cm": 30},
            "features": {"fsk_demod_snr": 15.2},
            "explanation_text": "调高频率测试", # Only 6 chars
            "raw_data_content": "VLC_RAW_RUN_003"
        }
        resp_bad2 = self.client.post("/api/runs", json=bad_payload_short_expl)
        self.assertEqual(resp_bad2.status_code, 200)
        self.assertFalse(resp_bad2.json()["is_valid_loop"])
        self.assertIn("机理解释字数不足", resp_bad2.json()["diff_summary"])

        # Strictly controlled single-variable change with valid explanation -> Accepted
        good_payload = {
            "team_id": "Team-01",
            "experiment_type": "vlc",
            "stage": "E3_Challenge",
            "parent_run_id": parent_id,
            "params": {"freq_hz": 800, "exposure_s": "0.0005", "dist_cm": 30},
            "features": {"fsk_demod_snr": 15.2},
            "explanation_text": "在保持物距与曝光时间固定下，将载波频率提升至800Hz验证条纹奈奎斯特极限。",
            "raw_data_content": "VLC_RAW_RUN_004"
        }
        resp_good = self.client.post("/api/runs", json=good_payload)
        self.assertEqual(resp_good.status_code, 200)
        self.assertTrue(resp_good.json()["is_valid_loop"])
        self.assertIn("有效单变量调整循环已确认", resp_good.json()["diff_summary"])

        valid_run_id = resp_good.json()["run_id"]

        # Test Diff View API
        resp_diff = self.client.get(f"/api/diff/{valid_run_id}")
        self.assertEqual(resp_diff.status_code, 200)
        diff_data = resp_diff.json()
        self.assertTrue(diff_data["has_parent"])
        self.assertEqual(diff_data["parent_run_id"], parent_id)
        self.assertTrue(diff_data["parameter_diffs"]["freq_hz"]["changed"])
        self.assertFalse(diff_data["parameter_diffs"]["dist_cm"]["changed"])
        self.assertTrue(diff_data["is_valid_loop"])

    def test_06_teacher_telemetry_and_export(self):
        """Test Teacher Dashboard metrics aggregation and student evidence export."""
        resp_dash = self.client.get("/api/teacher/dashboard")
        self.assertEqual(resp_dash.status_code, 200)
        dash = resp_dash.json()
        self.assertIn("dashboard", dash)
        self.assertEqual(len(dash["dashboard"]), 12)

        # Find Team-01
        t01 = next(t for t in dash["dashboard"] if t["team_id"] == "Team-01")
        self.assertTrue(t01["preflight_passed"])
        self.assertGreaterEqual(t01["total_runs"], 3)
        self.assertGreaterEqual(t01["valid_inquiry_loops"], 1)
        self.assertEqual(t01["current_stage"], "E3_Challenge")

        # Test Evidence Export JSON for ABET review
        resp_export = self.client.get("/api/export/Team-01")
        self.assertEqual(resp_export.status_code, 200)
        pkg = resp_export.json()
        self.assertEqual(pkg["export_metadata"]["course"], "EE3042L")
        self.assertEqual(pkg["export_metadata"]["team_id"], "Team-01")
        self.assertEqual(len(pkg["export_metadata"]["members"]), 4)
        self.assertEqual(pkg["preflight_audit"]["all_passed"], 1)
        self.assertGreaterEqual(len(pkg["runs_ledger"]), 3)
        for run in pkg["runs_ledger"]:
            self.assertIn("sha256", run)
            self.assertIn("is_valid_loop", run)
            self.assertIn("diff_summary", run)

if __name__ == "__main__":
    unittest.main(verbosity=2)
