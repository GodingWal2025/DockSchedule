# GitHub Repository Setup Guide

## Option 1: Quick CLI Setup (Fastest - 1 minute)

### Step 1: Create a GitHub Personal Access Token
1. Go to https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Select scope: `repo` (full control of private repositories)
4. Generate and copy the token

### Step 2: Create the Repo via API
Replace `YOUR_TOKEN` and `YOUR_USERNAME`:

```bash
# Set your credentials
export GITHUB_TOKEN="YOUR_TOKEN"
export GITHUB_USER="YOUR_USERNAME"
export REPO_NAME="amb-driver-log"

# Create the repository (private)
curl -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  -d '{"name":"'$REPO_NAME'","private":true,"description":"AMB Driver Log - Warehouse driver appointment and dock management system"}' \
  https://api.github.com/user/repos

# Create the repository (public - change to public: true)
curl -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  -d '{"name":"'$REPO_NAME'","private":false,"description":"AMB Driver Log - Warehouse driver appointment and dock management system"}' \
  https://api.github.com/user/repos
```

### Step 3: Push the Code
```bash
cd /path/to/amb_driver_log

# Add the GitHub remote
git remote add origin https://$GITHUB_USER:$GITHUB_TOKEN@github.com/$GITHUB_USER/$REPO_NAME.git

# Push everything
git push -u origin main
```

---

## Option 2: Web UI Setup (No CLI needed)

### Step 1: Create Repo on GitHub Website
1. Go to https://github.com/new
2. Repository name: `amb-driver-log`
3. Description: `AMB Driver Log - Warehouse driver appointment and dock management system`
4. Choose: Public or Private
5. **IMPORTANT**: Do NOT initialize with README, .gitignore, or LICENSE (we already have these)
6. Click "Create repository"

### Step 2: Push from Your Computer
```bash
cd /path/to/amb_driver_log

# Add the remote (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/amb-driver-log.git

# Push
git push -u origin main
```

---

## Option 3: GitHub Desktop / VS Code

1. Open the project folder in GitHub Desktop or VS Code
2. Go to "Publish repository" or "Initialize Repository"
3. Sign in to GitHub when prompted
4. Set repository name: `amb-driver-log`
5. Choose public/private
6. Publish

---

## Post-Setup: Clone on Other Machines

Once the repo is on GitHub, other team members can clone it:

```bash
git clone https://github.com/YOUR_USERNAME/amb-driver-log.git
cd amb-driver-log
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_data
python manage.py runserver
```

## Post-Setup: Server Deployment

On the warehouse server:
```bash
git clone https://github.com/YOUR_USERNAME/amb-driver-log.git /var/www/amb-driver-log
cd /var/www/amb-driver-log
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_data
# Then configure gunicorn/systemd as per README.md
```
