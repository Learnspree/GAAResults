import boto3
import requests
import re

def lambda_handler(event, context):
    from_id = int(event.get('from'))
    to_id = int(event.get('to'))

    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('gaa-results-leagues-production')

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
                # print((text.replace("\n", " "))[:4000])

                if league_name:
                    print(f"Found league name for ID {league_id}: {league_name}")
                    table.put_item(Item={
                        'league_code': str(league_id),
                        'league_name': league_name,
                        'url': url
                    })
                else:
                    print(f"No league name found for ID {league_id}")
            else:
                print(f"HTTP {response.status_code} for ID {league_id}")
        except Exception as e:
            print(f"Error processing ID {league_id}: {str(e)}")
    
    return {'status': 'completed'}