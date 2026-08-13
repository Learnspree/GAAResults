import os
import boto3
import logging
from decimal import Decimal
from boto3.dynamodb.conditions import Key, Attr

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def _to_int(v):
    if v is None:
        return None
    if isinstance(v, (int, Decimal)):
        try:
            return int(v)
        except Exception:
            return None
    try:
        return int(str(v))
    except Exception:
        try:
            return int(float(str(v)))
        except Exception:
            return None


def lambda_handler(event, context):
    """For each league, compute wins/draws/losses per club and update the league-clubs table.

    Steps:
    - scan `leagues` table for league_code
    - query `league-clubs` table for clubs in that league
    - scan `league-results` table for results in that league where the club appears
    - compute wins/draws/losses and update the club record with these attributes
    """
    dynamodb = boto3.resource('dynamodb')
    leagues_table_name = os.environ.get('DYNAMODB_TABLE', 'gaa-results-leagues-production')
    clubs_table_name = os.environ.get('DYNAMODB_CLUBS_TABLE', leagues_table_name.replace('leagues', 'league-clubs'))
    results_table_name = os.environ.get('DYNAMODB_RESULTS_TABLE', leagues_table_name.replace('leagues', 'league-results'))

    leagues_table = dynamodb.Table(leagues_table_name)
    clubs_table = dynamodb.Table(clubs_table_name)
    results_table = dynamodb.Table(results_table_name)

    try:
        # iterate leagues (paginated)
        response = leagues_table.scan(ProjectionExpression="league_code, league_name")
        leagues = response.get('Items', [])

        while True:
            for league in leagues:
                league_code = league.get('league_code')
                league_name = league.get('league_name')
                logger.info(f"Processing league {league_code}: {league_name}")

                # get clubs for this league
                clubs_resp = clubs_table.query(KeyConditionExpression=Key('league_code').eq(league_code))
                clubs = clubs_resp.get('Items', [])

                for club in clubs:
                    team_code = club.get('team_code')
                    team_name = club.get('team_name')
                    wins = draws = losses = 0

                    # scan results for this league where this team appears as home or away
                    res_kwargs = {
                        'ProjectionExpression': "home_team,away_team,home_goals,home_points,away_goals,away_points,match_date",
                        'FilterExpression': Attr('league_code').eq(league_code) & (Attr('home_team').eq(team_name) | Attr('away_team').eq(team_name))
                    }
                    r = results_table.scan(**res_kwargs)
                    results = r.get('Items', [])

                    while True:
                        for match in results:
                            # parse scores
                            hg = _to_int(match.get('home_goals'))
                            hp = _to_int(match.get('home_points'))
                            ag = _to_int(match.get('away_goals'))
                            ap = _to_int(match.get('away_points'))

                            if hg is None or hp is None or ag is None or ap is None:
                                # skip matches without complete numeric scores
                                continue

                            home_total = hg * 3 + hp
                            away_total = ag * 3 + ap

                            if match.get('home_team') == team_name:
                                if home_total > away_total:
                                    wins += 1
                                elif home_total < away_total:
                                    losses += 1
                                else:
                                    draws += 1
                            elif match.get('away_team') == team_name:
                                if away_total > home_total:
                                    wins += 1
                                elif away_total < home_total:
                                    losses += 1
                                else:
                                    draws += 1

                        # pagination for results scan
                        if 'LastEvaluatedKey' in r:
                            r = results_table.scan(ExclusiveStartKey=r['LastEvaluatedKey'], **{k: res_kwargs[k] for k in res_kwargs if k != 'FilterExpression'})
                            results = r.get('Items', [])
                            continue
                        break

                    # Update the club record with computed stats
                    try:
                        clubs_table.update_item(
                            Key={'league_code': league_code, 'team_code': team_code},
                            UpdateExpression='SET wins = :w, draws = :d, losses = :l',
                            ExpressionAttributeValues={
                                ':w': wins,
                                ':d': draws,
                                ':l': losses
                            }
                        )
                        logger.info(f"Updated {league_code}/{team_code} -> wins={wins} draws={draws} losses={losses}")
                    except Exception as e:
                        logger.exception(f"Failed updating club {team_code} for league {league_code}: {e}")

            # pagination for leagues
            if 'LastEvaluatedKey' in response:
                response = leagues_table.scan(ProjectionExpression="league_code, league_name", ExclusiveStartKey=response['LastEvaluatedKey'])
                leagues = response.get('Items', [])
                continue
            break

        return {'status': 'completed'}
    except Exception as e:
        logger.exception(f"Error processing leagues: {e}")
        return {'status': 'failed', 'error': str(e)}

