# Docker Deployment on DigitalOcean Droplet

## Overview

Deploy SpecIdol to a DigitalOcean Droplet using Docker with automated GitHub Actions deployment.

## Architecture

- **Single Docker container** with nginx + Python relay using supervisord
- **Two ports exposed**: 80 (web), 8765 (WebSocket)
- **Clean separation**: Infrastructure doesn't force app changes
- **Manual deployment**: GitHub Actions workflow triggered on-demand

## SSH Keys Explained

You need **two different SSH key pairs**:

1. **Your personal SSH key** (for manual Droplet access):
   - Used when you SSH into the Droplet yourself
   - Added when creating the Droplet in DigitalOcean UI
   - Lets you run commands like `ssh root@YOUR_DROPLET_IP`

2. **GitHub Actions SSH key** (for automated deployments):
   - Used by GitHub Actions to SSH into Droplet and deploy
   - Generated separately (see setup steps below)
   - Private key stored in GitHub Secrets
   - Public key added to Droplet's `authorized_keys`

Both keys give SSH access to the same Droplet. One for you, one for GitHub.

## Setup

### 1. Create DigitalOcean Droplet

1. **Create Droplet:**
   - Go to DigitalOcean → Create → Droplets
   - Choose: Ubuntu 22.04 LTS
   - Plan: Basic ($4/mo minimum)
   - Choose datacenter region
   - **Authentication:** Add your personal SSH key (or create one if you don't have it)
   - Create Droplet

2. **SSH into Droplet:**
   ```bash
   ssh root@YOUR_DROPLET_IP
   ```

3. **Install Docker:**
   ```bash
   curl -fsSL https://get.docker.com | sh
   ```

   If you get "Could not get lock" error, wait 1-2 minutes (Ubuntu runs automatic updates on first boot), then try again.

4. **Configure firewall:**
   ```bash
   ufw allow 22/tcp   # SSH (required or you'll lock yourself out)
   ufw allow 80/tcp   # Web interface (nginx serves static files)
   ufw allow 8765/tcp # WebSocket relay
   ufw enable
   # Type 'y' when prompted
   ```

5. **Clone repository:**
   ```bash
   mkdir -p /opt
   cd /opt
   git clone https://github.com/YOUR_USERNAME/SpecIdol.git specidol
   cd specidol
   ```

6. **Build and run Docker container:**
   ```bash
   docker build -t specidol .
   docker run -d --name specidol --restart unless-stopped -p 80:80 -p 8765:8765 specidol
   ```

   This single container runs:
   - nginx on port 80 (serves HTML/CSS/JS)
   - Python relay on port 8765 (WebSocket server)

7. **Verify it's running:**
   ```bash
   docker ps
   # Should see specidol container with both ports listed

   docker logs specidol
   # Should see nginx and relay startup messages
   ```

8. **Test deployment:**
   - Visit: `http://YOUR_DROPLET_IP`
   - Should see SpecIdol join screen

### 2. Configure GitHub Actions

1. **Generate SSH key for GitHub Actions (on your local machine):**
   ```bash
   ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/.ssh/specidol-github-actions
   # Press Enter twice (no passphrase)
   ```

   This creates two files:
   - `~/.ssh/specidol-github-actions` (private key - goes to GitHub)
   - `~/.ssh/specidol-github-actions.pub` (public key - goes to Droplet)

2. **Add public key to Droplet:**
   
   ```bash
   # Copy the public key
   cat ~/.ssh/specidol-github-actions.pub
   
   # SSH into Droplet with YOUR key
   ssh root@YOUR_DROPLET_IP
   
   # Add GitHub Actions public key
   echo "PASTE_PUBLIC_KEY_HERE" >> ~/.ssh/authorized_keys
   ```
   
3. **Add secrets to GitHub:**
   - Go to: GitHub repo → Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - Add two secrets:

     **Secret 1:**
     - **Name:** `DROPLET_HOST`
     - **Value:** Your Droplet IP address (e.g., `123.45.67.89`)

     **Secret 2:**
     - **Name:** `DROPLET_SSH_KEY`
     - **Value:** Contents of the **private** key file
       ```bash
       cat ~/.ssh/specidol-github-actions
       # Copy entire output including -----BEGIN and -----END lines
       ```

### 3. Deploy via GitHub Actions

1. **Push changes to GitHub:**
   ```bash
   git push origin main
   ```

2. **Trigger deployment:**
   - Go to: GitHub repo → Actions tab
   - Click: "Deploy to DigitalOcean Droplet"
   - Click: "Run workflow" → "Run workflow"

3. **Monitor deployment:**
   - Watch workflow progress in Actions tab
   - Check Droplet logs: `ssh root@YOUR_DROPLET_IP "docker logs -f specidol"`

## Workflow Details

The GitHub Actions workflow (`.github/workflows/deploy.yml`):
1. SSHs into Droplet using GitHub Actions key
2. Pulls latest code from GitHub
3. Stops running container
4. Rebuilds Docker image
5. Starts new container with `--restart unless-stopped`
6. Cleans up old Docker images

## Local Development

Use `make dev` for local development without Docker:

```bash
make dev        # Start relay + HTTP server
make dev-stop   # Stop servers
```

Or test with Docker locally:

```bash
make build      # Build Docker image
make servers    # Run container
make stop       # Stop container
```

## Monitoring

**View logs:**
```bash
ssh root@YOUR_DROPLET_IP
docker logs -f specidol
```

**Check container status:**
```bash
docker ps
```

**Restart container:**
```bash
docker restart specidol
```

## Backup

**Current limitation:** Sessions stored in-memory (lost on restart).

**Export/Import:**
- Controller has Import/Export buttons
- Manual backup before updates if needed

## Troubleshooting

**Container won't start:**
```bash
docker logs specidol
```

**Ports in use:**
```bash
lsof -i :80
lsof -i :8765
```

**GitHub Actions fails:**
- Check secrets are set correctly in GitHub
- Test SSH access: `ssh -i ~/.ssh/specidol-github-actions root@YOUR_DROPLET_IP`
- Check workflow logs in Actions tab

**WebSocket won't connect:**
- Verify port 8765 open: `ufw status`
- Check browser console for errors
- Confirm relay running: `docker exec specidol ps aux | grep relay`

## Cost

**DigitalOcean Droplet:**
- Basic plan: $4/mo (512MB RAM, 10GB disk)
- Recommended: $6/mo (1GB RAM, 25GB disk)
- Bandwidth: 500GB-1TB included

## Starting Fresh

If something breaks, just destroy and rebuild:

```bash
# On Droplet
docker stop specidol
docker rm specidol
docker rmi specidol
cd /opt/specidol
git pull origin main
docker build -t specidol .
docker run -d --name specidol --restart unless-stopped -p 80:80 -p 8765:8765 specidol
```

Or destroy the entire Droplet and start from Step 1.
