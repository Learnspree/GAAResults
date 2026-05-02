# GAAResults
Collect and analyse GAA results from Dublin GAA (sportlomo)

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

