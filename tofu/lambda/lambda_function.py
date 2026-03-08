import boto3
import requests
from bs4 import BeautifulSoup

def lambda_handler(event, context):
    from_id = int(event['from'])
    to_id = int(event['to'])
    
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('league-codes')
    
    for league_id in range(from_id, to_id + 1):
        url = f"https://dublingaa.sportlomo.com/league-2/{league_id}/"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                # span = soup.find('span', class_='titleBox active')
                span = soup.select_one('span.titleBox.active')
                if span:
                    print(f"Found league name for ID {league_id}: {span.text.strip()}")
                    league_name = span.text.strip()
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