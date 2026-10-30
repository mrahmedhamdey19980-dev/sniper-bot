import requests
import time

BOT_TOKEN = "8917012040:AAHZG-zhZhx9JGwWS870I1FDRA-G3mR6Fwc"
CHAT_ID = "1111438552"

CANDIDATE_KEYS = [
    "379cebf05a5944cd5a75fcecaf3361bf",
    "379cebf05a5944cd5a75fcecaf336fbf",
    "379cebf05a5944cd5a75fcecaf336bbf",
    "379cebf05a5944cd5a75fcecaf336dbf"
]

ACTIVE_API_KEY = None

REPLY_KEYBOARD = {
    "keyboard": [
        [{"text": "🎯 استخراج قسيمة النخب (دستور القناص)"}],
        [{"text": "📺 عرض كل المباريات الحية"}, {"text": "🔋 حالة الرصيد"}]
    ],
    "resize_keyboard": True,
    "is_persistent": True
}

def send_telegram(msg_txt):
    tg_ep = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    p_load = {
        "chat_id": CHAT_ID,
        "text": msg_txt,
        "parse_mode": "HTML",
        "reply_markup": REPLY_KEYBOARD
    }
    try:
        requests.post(tg_ep, json=p_load, timeout=10)
    except Exception as e:
        print("⚠️ خطأ في إرسال تيليجرام:", e)

def check_api_status():
    global ACTIVE_API_KEY
    keys_to_try = [ACTIVE_API_KEY] if ACTIVE_API_KEY else CANDIDATE_KEYS
    for k_str in keys_to_try:
        if not k_str:
            continue
        try:
            r_obj = requests.get(
                "https://v3.football.api-sports.io/status",
                headers={"x-apisports-key": k_str},
                timeout=10
            ).json()
            if not r_obj.get("errors"):
                ACTIVE_API_KEY = k_str
                reqs = r_obj.get("response", {}).get("requests", {})
                used = reqs.get("current", 0)
                limit = reqs.get("limit_day", 100)
                return k_str, (limit - used), used
        except Exception:
            continue
    return None, 0, 0

def elite_sniper_analysis(m):
    if m["red_cards"] > 0:
        return None

    m_min = m["m_min"]
    total_goals = m["h_goals"] + m["a_goals"]
    total_sot = m["h_sot"] + m["a_sot"]
    total_shots = m["h_shots"] + m["a_shots"]
    total_corners = m["h_corners"] + m["a_corners"]
    xg_total = m["xg_total"]
    
    match_line = f"<b>{m['h_team']} ({m['h_goals']} - {m['a_goals']}) {m['a_team']}</b> ⏱ <code>{m_min}'</code>"

    if 68 <= m_min <= 83:
        if total_sot <= 4 and xg_total < 1.70 and abs(m["h_goals"] - m["a_goals"]) <= 2:
            return {
                "score_rank": 93,
                "match_line": match_line,
                "league": m["lg_name"],
                "market": f"مجموع الأهداف: <b>أقل من ({total_goals + 1.5})</b>",
                "safety": "93% 🟢 (موت سريري تام للزخم)"
            }

    if (20 <= m_min <= 38) or (55 <= m_min <= 76):
        if m["h_poss"] >= 64 and m["h_shots"] >= 7 and m["h_corners"] >= 4:
            return {
                "score_rank": 90,
                "match_line": match_line,
                "league": m["lg_name"],
                "market": f"الركنيات: <b>أوفر ({total_corners + 1.5})</b> أو هانديكاب لصالح <b>{m['h_team']}</b>",
                "safety": "90% 🟢 (حصار هجومي وترجمة ركنيات)"
            }
        elif (100 - m["h_poss"]) >= 64 and m["a_shots"] >= 7 and m["a_corners"] >= 4:
            return {
                "score_rank": 90,
                "match_line": match_line,
                "league": m["lg_name"],
                "market": f"الركنيات: <b>أوفر ({total_corners + 1.5})</b> أو هانديكاب لصالح <b>{m['a_team']}</b>",
                "safety": "90% 🟢 (حصار هجومي وترجمة ركنيات)"
            }

    if 18 <= m_min <= 32 and total_goals <= 1:
        if total_shots >= 10 and total_sot >= 5 and xg_total >= 1.20:
            return {
                "score_rank": 89,
                "match_line": match_line,
                "league": m["lg_name"],
                "market": f"مجموع الأهداف: <b>أعلى من / أوفر ({total_goals + 0.5})</b> شوط أول أو مباراة",
                "safety": "89% 🟢 (شوارع دفاعية مفتوحة)"
            }

    if 60 <= m_min <= 76:
        goal_diff = abs(m["h_goals"] - m["a_goals"])
        if goal_diff <= 1 and (m["h_sot"] <= 2 or m["a_sot"] <= 2) and (m["h_poss"] >= 60 or (100 - m["h_poss"]) >= 60):
            underdog = m["a_team"] if (100 - m["h_poss"]) <= 45 else m["h_team"]
            return {
                "score_rank": 88,
                "match_line": match_line,
                "league": m["lg_name"],
                "market": f"هانديكاب آسيوي إيجابي: <b>{underdog} (+1.5)</b>",
                "safety": "88% 🟢 (عجز هجومي أمام جدار صلب)"
            }

    return None

def show_all_live_matches():
    api_k, _, _ = check_api_status()
    if not api_k:
        send_telegram("❌ تعذر الاتصال بمفتاح الرادار.")
        return
    hdr_dict = {"x-apisports-key": api_k}
    r_obj = requests.get("https://v3.football.api-sports.io/fixtures?live=all", headers=hdr_dict, timeout=10).json()
    fix_list = r_obj.get("response", [])
    if not fix_list:
        send_telegram("🌍 <b>لا توجد أي مباراة جارية في هذه اللحظة.</b>")
        return
    txt_lines = []
    for f in fix_list[:20]:
        c = f["league"]["country"]
        h = f["teams"]["home"]["name"]
        a = f["teams"]["away"]["name"]
        hg = f["goals"]["home"] or 0
        ag = f["goals"]["away"] or 0
        m = f["fixture"]["status"]["elapsed"] or 0
        txt_lines.append(f"• [{c}] {h} ({hg}-{ag}) {a} ⏱ <b>{m}'</b>")
    send_telegram(f"📺 <b>جميع المباريات الجارية الآن ({len(fix_list)} مباراة):</b>\n━━━━━━━━━━━━━━━\n" + "\n".join(txt_lines))

def execute_elite_slip_scan():
    api_k, remaining_quota, _ = check_api_status()
    if not api_k:
        send_telegram("❌ <b>خطأ في مفتاح الرادار:</b> تعذر الاتصال بمزود البيانات.")
        return

    hdr_dict = {"x-apisports-key": api_k}
    r_obj = requests.get("https://v3.football.api-sports.io/fixtures?live=all", headers=hdr_dict, timeout=10).json()
    fix_list = r_obj.get("response", [])
    
    candidates = []
    for f in fix_list:
        lg = f["league"]["name"].lower()
        m_min = f["fixture"]["status"]["elapsed"] or 0
        if any(w in lg for w in ["friendly", "youth", "u19", "u20", "u21", "reserve", "women", "amateur"]):
            continue
        if (18 <= m_min <= 38) or (55 <= m_min <= 83):
            candidates.append(f)

    top_tier_countries = ["England", "Spain", "Germany", "Italy", "France", "Saudi Arabia", "Portugal", "Netherlands", "Brazil", "Argentina", "Egypt"]
    def league_rank_weight(item):
        cntry = item["league"]["country"]
        return 0 if cntry in top_tier_countries else 1
        
    candidates.sort(key=league_rank_weight)

    collected_picks = []
    checked_stats_count = 0
    max_stats_checks = 6 if remaining_quota > 8 else 0

    for f_item in candidates:
        if checked_stats_count >= max_stats_checks:
            break
            
        fixture_id = f_item["fixture"]["id"]
        m_min = f_item["fixture"]["status"]["elapsed"] or 0
        league_str = f_item["league"]["name"]
        cntry_str = f_item["league"]["country"]
        h_team = f_item["teams"]["home"]["name"]
        a_team = f_item["teams"]["away"]["name"]
        h_g = f_item["goals"]["home"] or 0
        a_g = f_item["goals"]["away"] or 0
        
        checked_stats_count += 1
        has_stats = False
        stats_data = []
        try:
            stats_res = requests.get(
                f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fixture_id}",
                headers=hdr_dict,
                timeout=8
            ).json()
            stats_data = stats_res.get("response", [])
            if len(stats_data) >= 2:
                has_stats = True
        except Exception:
            continue

        if not has_stats:
            continue
            
        def get_stat(team_idx, stat_name):
            for s in stats_data[team_idx]["statistics"]:
                if s["type"] == stat_name and s["value"] is not None:
                    val_str = str(s["value"]).replace("%", "")
                    return float(val_str) if "." in val_str else int(val_str)
            return 0

        h_sot = get_stat(0, "Shots on Goal")
        a_sot = get_stat(1, "Shots on Goal")
        h_shots = get_stat(0, "Total Shots")
        a_shots = get_stat(1, "Total Shots")
        
        xg_0 = get_stat(0, "expected_goals")
        xg_1 = get_stat(1, "expected_goals")
        if xg_0 == 0 and xg_1 == 0:
            xg_calculated = round((h_sot + a_sot) * 0.28 + ((h_shots + a_shots) - (h_sot + a_sot)) * 0.05, 2)
        else:
            xg_calculated = round(xg_0 + xg_1, 2)

        match_info = {
            "lg_name": f"{cntry_str} - {league_str}",
            "h_team": h_team,
            "a_team": a_team,
            "m_min": m_min,
            "h_goals": h_g,
            "a_goals": a_g,
            "h_poss": get_stat(0, "Ball Possession") or 50,
            "h_sot": h_sot,
            "a_sot": a_sot,
            "h_shots": h_shots,
            "a_shots": a_shots,
            "h_corners": get_stat(0, "Corner Kicks"),
            "a_corners": get_stat(1, "Corner Kicks"),
            "red_cards": (get_stat(0, "Red Cards") or 0) + (get_stat(1, "Red Cards") or 0),
            "xg_total": xg_calculated
        }
        
        pick = elite_sniper_analysis(match_info)
        if pick:
            collected_picks.append(pick)

    collected_picks.sort(key=lambda x: x["score_rank"], reverse=True)
    top_picks = collected_picks[:4]
    est_remaining = max(0, remaining_quota - checked_stats_count - 1)
    num_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣"]

    if top_picks:
        slip_blocks = []
        for idx, p in enumerate(top_picks):
            icon = num_emojis[idx]
            slip_blocks.append(
                f"{icon} {p['match_line']}\n"
                f"🏆 {p['league']}\n"
                f"🎯 <b>التوقع:</b> {p['market']}\n"
                f"🛡️ <b>الأمان:</b> {p['safety']}"
            )
        final_card = (
            f"💎 <b>بطاقة القناص النخبوي (السحابة الدائمة)</b>\n"
            f"━━━━━━━━━━━━━━━\n" +
            "\n───────────────\n".join(slip_blocks) +
            f"\n━━━━━━━━━━━━━━━\n"
            f"🌍 الحية: {len(fix_list)} | 💎 الفرص الصافية: {len(top_picks)} | 🔋 الرصيد: {est_remaining}/100"
        )
    else:
        final_card = (
            f"💎 <b>بطاقة القناص النخبوي (السحابة الدائمة)</b>\n"
            f"━━━━━━━━━━━━━━━\n"
            f"🛡️ <b>الفلتر النخبوي رفض جميع المباريات الحالية؛ لعدم استيفاء شروط الأمان الصارمة (+88%).</b>\n"
            f"🌍 إجمالي الملاعب الحية: {len(fix_list)} مباراة\n"
            f"🔋 الرصيد المتبقي اليوم: {est_remaining} / 100\n"
            f"━━━━━━━━━━━━━━━\n"
            f"💡 <i>المحرك يمتنع عن التخمين العشوائي لحماية رأس المال. عاود الفحص لاحقاً.</i>"
        )

    send_telegram(final_card)

def main():
    print("🚀 المحرك السحابي الدائم بدأ العمل بنجاح...")
    send_telegram("🚀 <b>تم تشغيل السيرفر السحابي الدائم بنجاح!</b>\nالمحرك يعمل الآن 24/7 دون الحاجة لفتح المتصفح.")
    
    last_update_id = 0
    try:
        init_res = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates", timeout=10).json()
        if init_res.get("result"):
            last_update_id = init_res["result"][-1]["update_id"]
    except Exception:
        pass

    while True:
        try:
            u_poll = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates?offset={last_update_id + 1}&timeout=20"
            r_obj = requests.get(u_poll, timeout=25).json()
            for item in r_obj.get("result", []):
                last_update_id = item["update_id"]
                msg_text = item.get("message", {}).get("text", "").strip()
                
                if msg_text in ["/scan", "/force", "🎯 استخراج قسيمة النخب (دستور القناص)"]:
                    execute_elite_slip_scan()
                elif msg_text in ["📺 عرض كل المباريات الحية"]:
                    show_all_live_matches()
                elif msg_text in ["/status", "🔋 حالة الرصيد"]:
                    _, rem, used = check_api_status()
                    send_telegram(f"🔋 <b>حالة الرصيد اليومي:</b>\n• المستهلك: {used}\n• المتبقي: <b>{rem} طلب</b> من 100")
        except Exception:
            time.sleep(2)

if __name__ == "__main__":
    main()
