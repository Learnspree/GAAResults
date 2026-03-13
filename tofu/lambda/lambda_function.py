import os
import boto3
import requests
import re

def lambda_handler(event, context):
    from_id = int(event.get('from'))
    to_id = int(event.get('to'))

    dynamodb = boto3.resource('dynamodb')
    leagues_table_name = os.environ.get('DYNAMODB_TABLE', 'gaa-results-leagues-production')
    table = dynamodb.Table(leagues_table_name)

    # clubs table can be provided via env or derived from leagues table name
    clubs_table_name = os.environ.get('DYNAMODB_CLUBS_TABLE', leagues_table_name.replace('leagues', 'league-clubs'))
    clubs_table = dynamodb.Table(clubs_table_name)

    for league_id in range(from_id, to_id + 1):
        url = f"https://dublingaa.sportlomo.com/league-2/{league_id}/"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                text = response.text

                # Try to find the span directly in the HTML (server-rendered)
                m = re.search(r'<span[^>]*class=["\']titleBox(?:\s+active)?["\'][^>]*>(.*?)</span>', text, re.DOTALL | re.IGNORECASE)

                league_name = None
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

                # log a single-line, truncated HTML snippet for debugging
                # print((text.replace("\n", " ")))

                if league_name:
                    print(f"Found league name for ID {league_id}: {league_name}")

                    # extract first occurrence of processcell('MonDDYY') and take last two chars as year
                    m_year = re.search(r"processcell\(\s*['\"][A-Za-z]+[0-9]{1,2}([0-9]{2})['\"]\s*\)", text, re.IGNORECASE)
                    year = m_year.group(1) if m_year else '26'

                    # parse age-group like 'U14' from league_name
                    age_group = None
                    m_age = re.search(r"\bU(\d{1,2})\b", league_name, re.IGNORECASE)
                    if m_age:
                        age_group = 'U' + m_age.group(1)
                    elif re.search(r"adult", league_name, re.IGNORECASE):
                        age_group = 'Adult'
                    elif re.search(r"minor", league_name, re.IGNORECASE):
                        age_group = 'Minor'
                    else:
                        age_group = "Unknown"

                    # parse sport code (LGFA or Camogie)
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

                    # parse division like 'Div 10' or 'Division 9'
                    division = None
                    m_div = re.search(r"\b(?:Div|Division)\s+(\d{1,2})\b", league_name, re.IGNORECASE)
                    if m_div:
                        division = m_div.group(1)
                    else:
                        division = "0"

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

                    # Write to the league_clubs_table with league_code, club_code and club_name
                    # Only do this if the league sport_code is NOT 'Other' (to avoid parsing irrelevant pages)
                    if sport_code and sport_code != 'Other':
                        try:
                            # find all club links and collect unique club_code -> club_name
                            club_re = re.compile(r'<a\s+href=["\']https?://dublingaa\.sportlomo\.com/clubprofile/([^?"\']+)(?:\?[^"\']*)?["\'][^>]*>(.*?)</a>', re.IGNORECASE | re.DOTALL)
                            clubs = {}
                            for m in club_re.finditer(text):
                                club_code = m.group(1).strip()
                                club_name = re.sub(r"\s+", " ", m.group(2)).strip()
                                if club_code and club_code not in clubs:
                                    clubs[club_code] = club_name

                            for club_code, club_name in clubs.items():
                                try:
                                    clubs_table.put_item(Item={
                                        'league_code': str(league_id),
                                        'club_code': club_code,
                                        'club_name': club_name
                                    })
                                except Exception as e:
                                    print(f"Failed writing club {club_code} for league {league_id}: {e}")
                        except Exception as e:
                            print(f"Error parsing/writing clubs for league {league_id}: {e}")
                else:
                    print(f"No league name found for ID {league_id}")
            else:
                print(f"HTTP {response.status_code} for ID {league_id}")
        except Exception as e:
            print(f"Error processing ID {league_id}: {str(e)}")
    
    return {'status': 'completed'}