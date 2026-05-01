#!/bin/bash
REPO="scchin/openclaw-soul-backups"
# Get all files in the repo
FILES=$(gh api /repos/$REPO/contents/ --paginate)

# Extract files that match today's backup pattern
# Pattern: soul_full_20260422_0906.tar.gz.part*
echo "🔍 Searching for today's backup fragments..."
echo "$FILES" | jq -c '.[] | select(.name | contains("soul_full_20260422_0906.tar.gz.part"))' > to_delete.jsonl

if [ ! -s to_delete.jsonl ]; then
    echo "✅ No matching files found to delete."
    exit 0
fi

echo "🚀 Starting REAL emergency deletion of cloud fragments..."
while read -r line; do
    NAME=$(echo "$line" | jq -r '.name')
    SHA=$(echo "$line" | jq -r '.sha')
    echo "Deleting $NAME (sha: $SHA)..."
    # Fix: Added -f message to comply with GitHub API requirements for deletion
    gh api -X DELETE "/repos/$REPO/contents/$NAME" -f sha="$SHA" -f message="Purging residue" > /dev/null
done < to_delete.jsonl

echo "✅ All identified fragments have been processed."
rm to_delete.jsonl
