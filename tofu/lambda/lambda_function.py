import os
import boto3
import requests
import re
import html

def lambda_handler(event, context):
    from_id = int(event.get('from'))
    to_id = int(event.get('to'))

    dynamodb = boto3.resource('dynamodb')
    leagues_table_name = os.environ.get('DYNAMODB_TABLE', 'gaa-results-leagues-production')
    clubs_table_name = os.environ.get('DYNAMODB_CLUBS_TABLE', leagues_table_name.replace('leagues', 'league-clubs'))
    results_table_name = os.environ.get('DYNAMODB_RESULTS_TABLE', leagues_table_name.replace('leagues', 'league-results'))
    table = dynamodb.Table(leagues_table_name)
    clubs_table = dynamodb.Table(clubs_table_name)
    results_table = dynamodb.Table(results_table_name)
    matches_table_name = os.environ.get('DYNAMODB_MATCHES_TABLE', leagues_table_name.replace('leagues', 'league-matches'))
    matches_table = dynamodb.Table(matches_table_name)

    for league_id in range(from_id, to_id + 1):
        url = f"https://dublingaa.sportlomo.com/league-2/{league_id}/"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                text = response.text
                # log a single-line, truncated HTML snippet for debugging
                # print((text.replace("\n", " ")))
                
                # Get League Name
                league_name = extract_league_name(text)

                if league_name:
                    print(f"Found league name for ID {league_id}: {league_name}")

                    # extract first occurrence of processcell('MonDDYY') and take last two chars as year
                    m_year = re.search(r"processcell\(\s*['\"][A-Za-z]+[0-9]{1,2}([0-9]{2})['\"]\s*\)", text, re.IGNORECASE)
                    year = m_year.group(1) if m_year else '26'

                    # parse age-group like 'U14' from league_name; fallback to 'Under X'
                    age_group = extract_age_group(league_name)

                    # parse sport code (LGFA or Camogie)
                    sport_code = extract_sport_code(league_name)

                    # parse division like 'Div 10' or 'Division 9'
                    division = extract_division(league_name)

                    item = {
                        'league_code': str(league_id),
                        'league_name': league_name,
                        'url': url,
                        'year': year,
                        'age_group': age_group,
                        'sport_code': sport_code,
                        'division': division
                    }

                    table.put_item(Item=item)

                    # Write to the league_clubs_table with league_code, team_code and team_name
                    # Only do this if the league sport_code is NOT 'Other' (to avoid parsing irrelevant pages)
                    # Had to comment out the "not other" part because some valid leagues don't identify the sport at all
                    if sport_code: # and sport_code != 'Other':
                        extract_league_clubs(clubs_table, league_id, text)
                        extract_league_results(results_table, league_id, text)
                        extract_league_matches(matches_table, league_id, text)
                else:
                    print(f"No league name found for ID {league_id}")
            else:
                print(f"HTTP {response.status_code} for ID {league_id}")
        except Exception as e:
            print(f"Error processing ID {league_id}: {str(e)}")
    
    return {'status': 'completed'}

def extract_league_name(text):
    league_name = None
    
    # Try to find the span directly in the HTML (server-rendered)
    m = re.search(r'<span[^>]*class=["\']titleBox(?:\s+active)?["\'][^>]*>(.*?)</span>', text, re.DOTALL | re.IGNORECASE)

    if m:
        league_name = m.group(1).strip()
    else:
        # Fallback: match jQuery injection like:
        # jQuery(".entry-title").html('<span class="titleBox active">LGFA U15 League Div 1</span>');
        m2 = re.search(r"jQuery\(\s*['\"]\.entry-title['\"]\s*\)\.html\(\s*['\"](?P<html><span[^'\"]*?>.*?</span>)['\"]\s*\);", text, re.DOTALL | re.IGNORECASE)
        if m2:
            inner = re.search(r'>(.*?)</span>', m2.group('html'), re.DOTALL | re.IGNORECASE)
            if inner:
                league_name = inner.group(1).strip()
    return league_name

def extract_division(league_name):
    division = None
    m_div = re.search(r"\b(?:Div|Division)\s+(\d{1,2})\b", league_name, re.IGNORECASE)
    if m_div:
        division = m_div.group(1)
    else:
        division = "0"
    return division

def extract_age_group(league_name):
    age_group = None
    m_age = re.search(r"\bU(\d{1,2})\b", league_name, re.IGNORECASE)

    if m_age:
        age_group = 'U' + m_age.group(1)
    else:
        m_under = re.search(r"\bUnder\s+(\d{1,2})\b", league_name, re.IGNORECASE)
        if m_under:
            age_group = 'U' + m_under.group(1)
        elif re.search(r"adult", league_name, re.IGNORECASE):
            age_group = 'Adult'
        elif re.search(r"minor", league_name, re.IGNORECASE):
            age_group = 'Minor'
        else:
            age_group = "Unknown"
    return age_group

def extract_sport_code(league_name):
    sport_code = None
    if re.search(r"\bLGFA\b", league_name, re.IGNORECASE):
        sport_code = 'LGFA'
    elif re.search(r"camogie", league_name, re.IGNORECASE):
        sport_code = 'Camogie'
    elif re.search(r"football", league_name, re.IGNORECASE):
        sport_code = 'Football'
    elif re.search(r"hurling", league_name, re.IGNORECASE):
        sport_code = 'Hurling'
    else:
        sport_code = 'Other'
    return sport_code

def safe(s):
    """Sanitize a string: unescape HTML entities, strip tags and remove all whitespace."""
    t = html.unescape(s or "")
    t = re.sub(r"<.*?>", "", t)
    t = t.replace('\u00A0', ' ')
    # Only trim leading/trailing whitespace; preserve internal spacing
    t = t.strip()
    t = t.replace('|', '-')
    return t

def extract_league_clubs(clubs_table, league_id, text):
    try:
        # find all team links that include a team_id parameter and collect unique team_id -> team_name
        team_re = re.compile(r'<a\s+href=["\']https?://dublingaa\.sportlomo\.com/clubprofile/[^"\']*?team_id=(\d+)[^"\']*["\'][^>]*>(.*?)</a>', re.IGNORECASE | re.DOTALL)
        teams = {}
        for m in team_re.finditer(text):
            team_code = m.group(1).strip().rstrip('/')
            team_name = re.sub(r"\s+", " ", m.group(2)).strip()
            if team_code and team_code not in teams:
                teams[team_code] = team_name

        for team_code, team_name in teams.items():
            try:
                clubs_table.put_item(Item={
                                        'league_code': str(league_id),
                                        'team_code': team_code,
                                        'team_name': team_name
                                    })
            except Exception as e:
                print(f"Failed writing team {team_code} for league {league_id}: {e}")
    except Exception as e:
        print(f"Error parsing/writing teams for league {league_id}: {e}")

def extract_league_matches(matches_table, league_id, text):
    try:
        from datetime import datetime
        # Find desktop rows which contain full match details
        rows_re = re.compile(r'<tr[^>]*class=["\']desktop["\'][^>]*>(.*?)</tr>', re.IGNORECASE | re.DOTALL)
        for row_html in rows_re.findall(text):
            # extract team names (first team-name is home, second is away)
            team_name_re = re.compile(r'<span[^>]*class=["\']team-name["\'][^>]*>.*?<a[^>]*>(.*?)</a>.*?</span>', re.IGNORECASE | re.DOTALL)
            teams = team_name_re.findall(row_html)
            if len(teams) < 2:
                continue

            # normalize whitespace inside names, then sanitize
            raw_home = re.sub(r"\s+", " ", teams[0]).strip()
            raw_away = re.sub(r"\s+", " ", teams[1]).strip()
            home_team = safe(raw_home)
            away_team = safe(raw_away)

            # extract score cells (first score = home, second = away)
            score_td_re = re.compile(r'<td[^>]*class=["\']score["\'][^>]*>(.*?)</td>', re.IGNORECASE | re.DOTALL)
            scores = score_td_re.findall(row_html)
            if len(scores) < 2:
                continue

            def parse_score(s):
                s_text = re.sub(r'<.*?>', '', s or '')
                m = re.search(r"(\d+)\s*-\s*(\d+)", s_text)
                return (m.group(1), m.group(2)) if m else (None, None)

            home_goals, home_points = parse_score(scores[0])
            away_goals, away_points = parse_score(scores[1])

            # extract match time if present
            time_m = re.search(r'<td[^>]*class=["\']time["\'][^>]*>.*?<span[^>]*>(.*?)</span>', row_html, re.IGNORECASE | re.DOTALL)
            match_time = re.sub(r"\s+", " ", time_m.group(1)).strip() if time_m else None

            # attempt to find a date string in the row (e.g., '08 Jun 2025')
            date_m = re.search(r"(\d{1,2}\s+[A-Za-z]{3}\s+\d{4})", row_html)
            match_date = None
            if date_m:
                try:
                    dt = datetime.strptime(date_m.group(1).strip(), "%d %b %Y")
                    match_date = dt.strftime("%Y-%m-%d")
                except Exception:
                    match_date = date_m.group(1).strip()

            match_code = f"{home_team}-{away_team}-{match_date or 'nodate'}"
            # normalize match_code: remove non-alphanumeric and lowercase for a strict key
            match_code = re.sub(r"[^A-Za-z0-9]", "", match_code).lower()

            item = {
                'match_code': match_code,
                'league_code': str(league_id),
                'home_team': home_team,
                'away_team': away_team,
                'home_goals': home_goals,
                'home_points': home_points,
                'away_goals': away_goals,
                'away_points': away_points,
                'match_time': match_time,
                'match_date': match_date
            }

            try:
                matches_table.put_item(Item=item)
            except Exception as e:
                print(f"Failed writing match {match_code} for league {league_id}: {e}")
    except Exception as e:
        print(f"Error parsing/writing matches for league {league_id}: {e}")

# Save record in results table with league_code, home_team, away_team, home_goals, home_points, away_goals, away_points and match_date
def extract_league_results(results_table, league_id, text):
    import html
    from datetime import datetime
    try:
        # find all tooltip spans' title attribute (which contains encoded HTML with match info)
        tooltip_re = re.compile(r"<span[^>]*class=[\'\"]tooltip[\'\"][^>]*title=[\'\"](.*?)[\'\"][^>]*>", re.IGNORECASE | re.DOTALL)
        for title_html in tooltip_re.findall(text):
            decoded = html.unescape(title_html)

            # extract match date from <center>DATE</center> if present
            date_m = re.search(r"<center[^>]*>(.*?)</center>", decoded, re.IGNORECASE | re.DOTALL)
            match_date = None
            if date_m:
                date_str = re.sub(r"\s+", " ", date_m.group(1)).strip()
                try:
                    dt = datetime.strptime(date_str, "%d %b %Y")
                    match_date = dt.strftime("%Y-%m-%d")
                except Exception:
                    match_date = date_str

            # extract home/away teams and scores from the decoded HTML
            # remove any <center>...</center> (match date) so it doesn't get appended to the away team
            decoded_for_scores = re.sub(r"<center[^>]*>.*?</center>", "", decoded, flags=re.IGNORECASE | re.DOTALL)

            # expected structure (after removing center):
            # [HOME TEAM] <b>Hgoals - Hpoints</b> VS <b>Agoals - Apoints</b> [AWAY TEAM]
            score_re = re.compile(r"^(.*?)\s*<b>\s*(\d+)\s*-\s*(\d+)\s*</b>\s*VS\s*<b>\s*(\d+)\s*-\s*(\d+)\s*</b>\s*(.*?)$", re.IGNORECASE | re.DOTALL)
            m = score_re.search(decoded_for_scores)
            if not m:
                print(f"Error parsing match info from tooltip: {decoded}")
                continue

            home_team = safe(re.sub(r"<.*?>", "", m.group(1)))
            home_goals = m.group(2)
            home_points = m.group(3)
            away_goals = m.group(4)
            away_points = m.group(5)
            away_team = safe(re.sub(r"<.*?>", "", m.group(6)))

            match_code = f"{league_id}-{home_team}-{away_team}-{match_date}"
            # normalize match_code: remove non-alphanumeric and lowercase for a strict key
            match_code = re.sub(r"[^A-Za-z0-9]", "", match_code).lower()


            item = {
                'match_code': match_code,
                'league_code': str(league_id),
                'home_team': home_team,
                'away_team': away_team,
                'home_goals': home_goals,
                'home_points': home_points,
                'away_goals': away_goals,
                'away_points': away_points,
                'match_date': match_date
            }

            try:
                results_table.put_item(Item=item)
            except Exception as e:
                print(f"Failed writing result for league {league_id}: {e}")
    except Exception as e:
        print(f"Error parsing/writing results for league {league_id}: {e}")