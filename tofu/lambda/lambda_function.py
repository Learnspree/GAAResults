import os
import boto3
import requests
import re

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

# TODO - update this function to extract match results using a different regex
# EXAMPLE: <td style='max-width:30px;min-width:30px'><span class='tooltip' title='&lt;div style=&#039;display:inline-block;color:#000;font-family: Arial, &quot;Helvetica Neue&quot;, Helvetica, sans-serif;&#039;&gt;Innisfails&amp;nbsp;&amp;nbsp;&lt;b&gt;5 - 10&lt;/b&gt; VS &lt;b&gt;3 - 4&lt;/b&gt; Tyrrelstown&lt;/div&gt;&lt;center style=&#039;color:#000;font-family: Arial, &quot;Helvetica Neue&quot;, Helvetica, sans-serif;&#039;&gt;08 Jun 2025&lt;/center&gt;&lt;/span&gt;' style='background:#0CD68A; text-align:center; color:#fff;'>W</span></td>
# TEMPLATE: <td style='max-width:30px;min-width:30px'><span class='tooltip' title='&lt;div style=&#039;display:inline-block;color:#000;font-family: Arial, &quot;Helvetica Neue&quot;, Helvetica, sans-serif;&#039;&gt;[HOME TEAM]&amp;nbsp;&amp;nbsp;&lt;b&gt;[HOME TEAM GOALS] - [HOME TEAM POINTS]0&lt;/b&gt; VS &lt;b&gt;[AWAY TEAM GOALS] - [AWAY TEAM POINTS]&lt;/b&gt; [AWAY TEAM]&lt;/div&gt;&lt;center style=&#039;color:#000;font-family: Arial, &quot;Helvetica Neue&quot;, Helvetica, sans-serif;&#039;&gt;[MATCH DATE]&lt;/center&gt;&lt;/span&gt;' style='background:#0CD68A; text-align:center; color:#fff;'>W</span></td>
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
            # expected structure: [HOME TEAM] <b>Hgoals - Hpoints</b> VS <b>Agoals - Apoints</b> [AWAY TEAM]
            score_re = re.compile(r"^(.*?)\s*<b>\s*(\d+)\s*-\s*(\d+)\s*</b>\s*VS\s*<b>\s*(\d+)\s*-\s*(\d+)\s*</b>\s*(.*?)$", re.IGNORECASE | re.DOTALL)
            m = score_re.search(decoded)
            if not m:
                continue

            # TODO - parse out all whitespace and HTML
            def _safe(s):
                return re.sub(r"\s+", " ", s).strip().replace('|', '-')

            home_team = _safe(re.sub(r"<.*?>", "", m.group(1)))
            home_goals = m.group(2)
            home_points = m.group(3)
            away_goals = m.group(4)
            away_points = m.group(5)
            away_team = _safe(re.sub(r"<.*?>", "", m.group(6)))
            match_code = f"{league_id}-{_safe(home_team)}-{_safe(away_team)}"


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