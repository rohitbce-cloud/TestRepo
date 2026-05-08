@echo off
cd /d C:\Rohit\Project\GithubDoc
git init
git add .
git commit -m "Add AI Engineering Agent"
echo.
echo Now run these manually:
echo 1. Create a GitHub repo at https://github.com/new
echo 2. git remote add origin https://github.com/yourusername/yourrepo.git
echo 3. git push -u origin main
echo 4. Add secrets OPENAI_API_KEY and GITHUB_TOKEN in GitHub Actions
echo 5. Create a PR to trigger the agent