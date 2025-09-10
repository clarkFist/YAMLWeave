#!/bin/bash

echo "Starting GitHub sync with retry mechanism..."

MAX_ATTEMPTS=20
INITIAL_WAIT=5
current_wait=$INITIAL_WAIT

for i in $(seq 1 $MAX_ATTEMPTS); do
    echo ""
    echo "=== Attempt $i of $MAX_ATTEMPTS ==="
    echo "Waiting $current_wait seconds before attempt..."
    sleep $current_wait
    
    echo "Trying to push to GitHub..."
    git push -u origin main --ipv4
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "*** SUCCESS! Repository synced successfully ***"
        git status
        git log --oneline -3
        exit 0
    fi
    
    echo "Push failed, trying fetch first..."
    timeout 60 git fetch origin main --ipv4
    
    if [ $? -eq 0 ]; then
        echo "Fetch successful, trying merge..."
        git merge origin/main --allow-unrelated-histories --no-edit
        
        if [ $? -eq 0 ]; then
            echo "Merge successful, trying push again..."
            git push -u origin main --ipv4
            
            if [ $? -eq 0 ]; then
                echo ""
                echo "*** SUCCESS! Repository synced after merge ***"
                git status
                git log --oneline -3
                exit 0
            fi
        fi
    fi
    
    echo "Attempt $i failed. Exponential backoff..."
    current_wait=$((current_wait * 2))
    if [ $current_wait -gt 120 ]; then
        current_wait=120
    fi
done

echo ""
echo "All $MAX_ATTEMPTS attempts failed. Please check:"
echo "1. Network connectivity"
echo "2. GitHub repository access"
echo "3. DNS settings"
exit 1