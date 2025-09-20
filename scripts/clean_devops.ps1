Write-Host "🧹 Cleaning AI-Augmented DevOps Environment..."

# --- Stop and remove Docker containers/images ---
Write-Host "Stopping all Docker containers..."
docker stop $(docker ps -aq) 2>$null

Write-Host "Removing all Docker containers..."
docker rm -f $(docker ps -aq) 2>$null

Write-Host "Removing all Docker images..."
docker rmi -f $(docker images -q) 2>$null

Write-Host "Pruning Docker system (cache, volumes)..."
docker system prune -af --volumes

# --- Clean Jenkins Workspace ---
$jenkinsWorkspace = "C:\ProgramData\Jenkins\.jenkins\workspace\AI-Augmented-DevOps"
if (Test-Path $jenkinsWorkspace) {
    Write-Host "Removing Jenkins workspace at $jenkinsWorkspace ..."
    Remove-Item -Recurse -Force $jenkinsWorkspace
} else {
    Write-Host "No Jenkins workspace found at $jenkinsWorkspace."
}

Write-Host "Cleanup complete. Ready for fresh build!"