import os
import re
import sys

abs_path = os.path.dirname(__file__)
# /Python-Project'
main_cwd = re.sub('crawl_data.*','crawl_data',abs_path)
os.chdir(main_cwd)
sys.path.append(main_cwd)

import json
import pandas as pd
import requests
from w88_bti_market.selenium_w88 import get_ct_tokens
from functions.sql_lite import SQLiteDB
import pytz
from datetime import datetime, timedelta


url = "https://prod20262.442hattrick.com/api/eventlist/asia/leagues/v2/1/live"

params = {
    "leagueIds": "4508,243,343,297448518724108288,290305635567026176,269,282,277,239181187774726144,218879693880041472"
}

tokens = get_ct_tokens("https://www.w88kaya.com/Sports/Launcher?provider=btiSports&game=btiSports&t=1&f=0&matchId=")

token = tokens["CT_APP_AUTHORIZATION"]
session_token = tokens["CT_APP_SESSION"]

headers = {
    "accept": "application/json",
    "accept-language": "en-US,en;q=0.9",
    "authorization": token,
    "priority": "u=1, i",
    "referer": "https://prod20262.442hattrick.com/vi/asian-view/live/",
    "session": session_token,
    "user-agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/149.0.0.0 Safari/537.36 Edg/149.0.0.0"
    ),
}

# cookies = {
#     "operatorToken": "logout",
#     "session": "YOUR_SESSION_TOKEN",
#     "authorization": "YOUR_AUTHORIZATION_TOKEN",
# }

response = requests.get(
    url,
    params=params,
    headers=headers,
    # cookies=cookies,
    timeout=30
)

print("Status:", response.status_code)

try:
    data = response.json()
    print(data)
except Exception:
    print(response.text)
    
    
 
def parse_matches(data: dict) -> pd.DataFrame:
    rows = []
    for league in data["serializedData"]:
        league_id    = league[0]
        league_name  = league[1]
        country_code = league[6]
        country_name = league[7]
        match_list   = league[12] if len(league) > 12 and isinstance(league[12], list) else []
 
        for match in match_list:
            if not isinstance(match, list):
                continue
            match_id   = match[0]
            teams      = match[1]
            home_team  = teams[0][1].get("VI") if teams else None
            away_team  = teams[1][1].get("VI") if teams and len(teams) > 1 else None
            match_name = match[2]
            kick_off   = match[3]
            sb         = match[4]
            home_score = int(sb[0]) if sb and sb[0] is not None else None
            away_score = int(sb[1]) if sb and sb[1] is not None else None
            stats      = sb[3] if sb and len(sb) > 3 and isinstance(sb[3], dict) else {}
            is_live    = match[5] if len(match) > 5 else None
            li         = match[7] if len(match) > 7 and isinstance(match[7], list) else []
            is_running   = li[0] if li else None
            elapsed_secs = li[2] if len(li) > 2 else None
            period       = li[3] if len(li) > 3 else None   # 23=H1, 24=H2, 25=FT
 
            rows.append({
                "match_id":             match_id,
                "match_name":           match_name,
                "kick_off_utc":         kick_off,
                "league_id":            league_id,
                "league_name":          league_name,
                "country_code":         country_code,
                "country_name":         country_name,
                "home_team":            home_team,
                "away_team":            away_team,
                "home_score":           home_score,
                "away_score":           away_score,
                "home_score_h1":        stats.get("firstHalfScore1"),
                "away_score_h1":        stats.get("firstHalfScore2"),
                "home_score_h2":        stats.get("secondHalfScore1"),
                "away_score_h2":        stats.get("secondHalfScore2"),
                "is_live":              is_live,
                "is_running":           is_running,
                "elapsed_secs":         elapsed_secs,
                "period":               period,
                "home_shots":           stats.get("shotsTeam1"),
                "away_shots":           stats.get("shotsTeam2"),
                "home_shots_on_target": stats.get("shotsOnTargetTeam1"),
                "away_shots_on_target": stats.get("shotsOnTargetTeam2"),
                "home_corners":         stats.get("cornersTeam1"),
                "away_corners":         stats.get("cornersTeam2"),
                "home_yellow_cards":    stats.get("yellowCardsTeam1"),
                "away_yellow_cards":    stats.get("yellowCardsTeam2"),
                "home_red_cards":       stats.get("redCardsTeam1"),
                "away_red_cards":       stats.get("redCardsTeam2"),
                "home_fouls":           stats.get("foulsTeam1"),
                "away_fouls":           stats.get("foulsTeam2"),
                "home_throw_ins":       stats.get("throwInsTeam1"),
                "away_throw_ins":       stats.get("throwInsTeam2"),
                "home_goal_kicks":      stats.get("goalKicksTeam1"),
                "away_goal_kicks":      stats.get("goalKicksTeam2"),
            })
 
    df = pd.DataFrame(rows)
    df["kick_off_utc"] = pd.to_datetime(df["kick_off_utc"], errors="coerce", utc=True)
    num_cols = df.columns.difference(["match_id","match_name","kick_off_utc",
                                      "league_id","league_name","country_code",
                                      "country_name","home_team","away_team",
                                      "is_live","is_running"])
    df[num_cols] = df[num_cols].apply(pd.to_numeric, errors="coerce")
    return df

def _vi(obj):
    """Extract Vietnamese label from {VI: '...'} dict."""
    if isinstance(obj, dict):
        return obj.get("VI")
    return None
 
 
def parse_markets_and_outcomes(data: dict):
    """
    Parameters
    ----------
    data : dict   parsed JSON with top-level "serializedData"
 
    Returns
    -------
    df_markets  : pd.DataFrame
    df_outcomes : pd.DataFrame
    """
    market_rows  = []
    outcome_rows = []
 
    for league in data["serializedData"]:
        match_list = league[12] if len(league) > 12 and isinstance(league[12], list) else []
 
        for match in match_list:
            if not isinstance(match, list) or len(match) < 9:
                continue
 
            match_id = match[0]
 
            # match[8] is the live-betting block: [match_id, count, [], [markets]]
            live_block = match[8]
            if not isinstance(live_block, list) or len(live_block) < 4:
                continue
 
            # markets live in live_block[3]  (list of market blocks)
            markets_raw = live_block[3]
            if not isinstance(markets_raw, list):
                continue
 
            for mkt in markets_raw:
                if not isinstance(mkt, list) or len(mkt) < 8:
                    continue
 
                market_id          = mkt[0]
                market_name        = mkt[1]
                market_name_display= mkt[2]
                type_block         = mkt[3] if isinstance(mkt[3], list) else []
                market_type_code   = type_block[0] if type_block else None
                market_type_name   = type_block[1] if len(type_block) > 1 else None
                period_code        = type_block[2] if len(type_block) > 2 else None
                is_active          = mkt[8] if len(mkt) > 8 else None
 
                market_rows.append({
                    "market_id":           market_id,
                    "match_id":            match_id,          # FK → matches
                    "market_name":         market_name,
                    "market_name_display": market_name_display,
                    "market_type_code":    market_type_code,
                    "market_type_name":    market_type_name,
                    "period_code":         period_code,        # 1=FT, 39=live
                    "is_active":           is_active,
                })
 
                outcomes_raw = mkt[7]
                if not isinstance(outcomes_raw, list):
                    continue
 
                for out in outcomes_raw:
                    if not isinstance(out, list) or len(out) < 6:
                        continue
 
                    odds_fmt   = out[6] if len(out) > 6 and isinstance(out[6], list) else []
                    limits     = out[14] if len(out) > 14 and isinstance(out[14], list) else []
 
                    outcome_rows.append({
                        "outcome_id":          out[0],
                        "market_id":           market_id,     # FK → markets
                        "match_id":            match_id,      # FK → matches
                        # Labels
                        "label_short":         _vi(out[1]),
                        "label_full":          _vi(out[2]),
                        "display_label":       _vi(out[9]) if len(out) > 9 else None,
                        # Odds
                        "is_highlighted":      out[4] if len(out) > 4 else None,
                        "decimal_odds":        out[5] if len(out) > 5 else None,
                        "american_odds":       odds_fmt[0] if odds_fmt else None,
                        "fractional_odds":     odds_fmt[2] if len(odds_fmt) > 2 else None,
                        "malay_odds":          odds_fmt[3] if len(odds_fmt) > 3 else None,
                        "indo_odds":           odds_fmt[4] if len(odds_fmt) > 4 else None,
                        "hk_odds":             odds_fmt[5] if len(odds_fmt) > 5 else None,
                        # Categorisation
                        "outcome_type_code":   out[8]  if len(out) > 8  else None,
                        # 1 = home / over
                        # 2 = draw / handicap-line
                        # 3 = away / under
                        "sort_order":          out[7]  if len(out) > 7  else None,
                        "line_value":          out[13] if len(out) > 13 else None,
                        # Bet limits
                        "min_bet":             limits[0] if limits else None,
                        "max_bet":             limits[1] if len(limits) > 1 else None,
                    })
 
    df_markets  = pd.DataFrame(market_rows)
    df_outcomes = pd.DataFrame(outcome_rows)
 
    # Cast numerics
    for col in ["decimal_odds", "line_value", "min_bet", "max_bet"]:
        if col in df_outcomes.columns:
            df_outcomes[col] = pd.to_numeric(df_outcomes[col], errors="coerce")
 
    return df_markets, df_outcomes


df = parse_matches(data)
print(df.head(5))

df1, df2 = parse_markets_and_outcomes(data)
print(df1.head(5))
print(df2.head(5))

hcm_tz = pytz.timezone('Asia/Ho_Chi_Minh')
current_date = datetime.now(hcm_tz) 
current_date_format_str = current_date.strftime('%Y%m%d') 
current_date_format = current_date.strftime('%Y-%m-%d') 
current_date_timestamp = current_date.strftime('%Y-%m-%d %H:%M:%S') 

df['run_timestamp'] = current_date_timestamp
df1['run_timestamp'] = current_date_timestamp
df2['run_timestamp'] = current_date_timestamp

db = SQLiteDB("./w88_bti_market/w88.db")

# db.write_df(df, "matches", index=False)
# db.write_df(df1, "markets", index=False)
# db.write_df(df2, "outcomes", index=False)

db.save_df(df, "matches", index=False)
db.save_df(df1, "markets_2", index=False)
db.save_df(df2, "outcomes", index=False)