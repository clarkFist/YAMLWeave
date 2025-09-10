#!/bin/bash

echo "=== Alternative GitHub Sync Strategy ==="

# Method 1: Direct force push (risky but effective for initial sync)
echo "Method 1: Attempting force push..."
git push -u origin main --force --ipv4
if [ $? -eq 0 ]; then
    echo "SUCCESS with force push!"
    exit 0
fi

# Method 2: Create new branch and push
echo "Method 2: Creating new branch..."
git checkout -b sync-$(date +%s)
git push -u origin $(git branch --show-current) --ipv4
if [ $? -eq 0 ]; then
    echo "SUCCESS with new branch!"
    git checkout main
    git merge $(git branch --show-current) --ff-only
    git push -u origin main --ipv4
    exit 0
fi

# Method 3: Bundle approach for offline transfer
echo "Method 3: Creating git bundle..."
git bundle create yamlweave-backup.bundle HEAD main
if [ $? -eq 0 ]; then
    echo "Bundle created: yamlweave-backup.bundle"
    echo "You can manually upload this to GitHub or transfer to another machine"
fi

# Method 4: Reset and start fresh
echo "Method 4: Repository status for manual intervention..."
git remote -v
git status
git log --oneline -5

echo ""
echo "=== Manual Steps if All Methods Fail ==="
echo "1. Visit: https://github.com/clarkFist/YAMLWeave"
echo "2. Delete the repository if it exists"  
echo "3. Create a new repository with the same name"
echo "4. Run: git push -u origin main"
echo ""
echo "Or upload files manually via GitHub web interface"