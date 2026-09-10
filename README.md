# GAAResults
Collect and analyse GAA results from Dublin GAA (sportlomo)

# API Definition

The API Gateway REST API is defined in `tofu/api/openapi.yaml` and imported by
OpenTofu. The current integrations return dummy data; DynamoDB integrations
will replace them later. Every endpoint requires the `x-api-key` header.

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | /competitions | Get list of all competitions with associated details like age group, year & URL link to the GAA website |
| GET | /clubs | Get list of all clubs |
| GET | /teams | Get list of all teams (a club can have multiple unique teams defined by team-id) |
| GET | /competitions/{competition_id}/teams | Get list of all teams in the competition |
| GET | /competitions/{competition_id}/matches | Get detailed list of all matches in the competition including home-team, away-team, home-goals, away-goals, home-total-points, away-total-goals, result (home-team, away-team or draw), referee, venue, date and time |

After applying the OpenTofu configuration, retrieve the unified API base URL and
key:

```sh
cd tofu
tofu output gaa_results_unified_api_url
tofu output -raw gaa_results_api_key_value
```

Example request:

```sh
curl -H "x-api-key: <api-key>" \
  "$(tofu output -raw gaa_results_unified_api_url)/competitions"
```

The unified API URL is served through the Angular site's CloudFront hostname
under `/api`. CloudFront removes that prefix before forwarding the request to
API Gateway, so the API Gateway stage and resource paths remain unchanged.



# Convert DynamoDB table to CSV for Quicksight Analysis

## League Table
```sh
aws dynamodb scan \
  --table-name gaa-results-leagues-production \
  --select ALL_ATTRIBUTES \
  --page-size 500 \
  --output json \
| jq -r '
  .Items as $items
  | ($items | map(keys[]) | unique) as $keys
  | $keys,
    ($items[] |
      [$keys[] as $k |
        ((.[$k] // {}) as $v |
          ($v.S // $v.N //
           (if ($v.BOOL?) then ($v.BOOL|tostring) else empty end) //
           (($v.SS // []) | join(";")) //
           (($v.NS // []) | join(";")) //
           ($v.B // "") //
           (($v.M // {}) | tostring) //
           (($v.L // []) | tostring) //
           "")
        )
      ]
    )
  | @csv
' > gaa-results-leagues-production.csv
```

## League Match Info Table
```sh
aws dynamodb scan \
  --table-name gaa-results-league-matches-production \
  --select ALL_ATTRIBUTES \
  --page-size 500 \
  --output json \
| jq -r '
  .Items as $items
  | ($items | map(keys[]) | unique) as $keys
  | $keys,
    ($items[] |
      [$keys[] as $k |
        ((.[$k] // {}) as $v |
          ($v.S // $v.N //
           (if ($v.BOOL?) then ($v.BOOL|tostring) else empty end) //
           (($v.SS // []) | join(";")) //
           (($v.NS // []) | join(";")) //
           ($v.B // "") //
           (($v.M // {}) | tostring) //
           (($v.L // []) | tostring) //
           "")
        )
      ]
    )
  | @csv
' > gaa-results-league-matches-production.csv
```

## League Results Info Table
```sh
aws dynamodb scan \
  --table-name gaa-results-league-results-production \
  --select ALL_ATTRIBUTES \
  --page-size 500 \
  --output json \
| jq -r '
  .Items as $items
  | ($items | map(keys[]) | unique) as $keys
  | $keys,
    ($items[] |
      [$keys[] as $k |
        ((.[$k] // {}) as $v |
          ($v.S // $v.N //
           (if ($v.BOOL?) then ($v.BOOL|tostring) else empty end) //
           (($v.SS // []) | join(";")) //
           (($v.NS // []) | join(";")) //
           ($v.B // "") //
           (($v.M // {}) | tostring) //
           (($v.L // []) | tostring) //
           "")
        )
      ]
    )
  | @csv
' > gaa-results-league-results-production.csv
```

## League Clubs Info Table
```sh
aws dynamodb scan \
  --table-name gaa-results-league-clubs-production \
  --select ALL_ATTRIBUTES \
  --page-size 500 \
  --output json \
| jq -r '
  .Items as $items
  | ($items | map(keys[]) | unique) as $keys
  | $keys,
    ($items[] |
      [$keys[] as $k |
        ((.[$k] // {}) as $v |
          ($v.S // $v.N //
           (if ($v.BOOL?) then ($v.BOOL|tostring) else empty end) //
           (($v.SS // []) | join(";")) //
           (($v.NS // []) | join(";")) //
           ($v.B // "") //
           (($v.M // {}) | tostring) //
           (($v.L // []) | tostring) //
           "")
        )
      ]
    )
  | @csv
' > gaa-results-league-clubs-production.csv
```
