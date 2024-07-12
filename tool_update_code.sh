#!/bin/bash

# Save current branch name
current_branch=$(git rev-parse --abbrev-ref HEAD)

# Stash any uncommitted changes
git stash

# Fetch all branches from the remote
git fetch --all

# Loop through all branches
for branch in $(git branch -r | grep -v '\->'); do
    # Remove the "origin/" part to get the local branch name
    local_branch=${branch#origin/}

    # Checkout the local branch
    git checkout $local_branch

    # Merge changes from the corresponding remote branch
    git merge $branch

    # You can add your chmod commands here if you want them to apply to each branch
    # chmod +x Source/Dashboard.py
    # chmod +x Source/Dashboard_headless.py
done

# Checkout the original branch
git checkout $current_branch

# Apply stashed changes
git stash pop
