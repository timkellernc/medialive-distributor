# Deployment Checklist

Use this checklist when deploying MediaLive Distributor to production.

## Pre-Deployment

### System Requirements
- [ ] Docker 20.10+ installed
- [ ] Docker Compose 2.0+ installed
- [ ] 10GbE network configured
- [ ] Sufficient CPU (8+ cores recommended)
- [ ] 8GB+ RAM available
- [ ] 10GB+ disk space free

### Network Configuration
- [ ] Static IP assigned to server
- [ ] Firewall configured:
  - [ ] Port 8000/tcp open (Web UI/API)
  - [ ] Ports 5000-5025/udp open (RTP inputs)
  - [ ] Outbound connections allowed for SRT/RTMP
- [ ] MediaLive security groups allow traffic to your server
- [ ] UDP buffer sizes increased (if needed):
  ```bash
  sudo sysctl -w net.core.rmem_max=134217728
  sudo sysctl -w net.core.rmem_default=134217728
  ```

### Files Ready
- [ ] All project files copied to server
- [ ] Directory: `/opt/medialive-distributor` or similar
- [ ] Correct permissions set
- [ ] Configuration directory created

## Deployment

### Docker Deployment
- [ ] Navigate to project directory
  ```bash
  cd /opt/medialive-distributor
  ```
- [ ] Review docker-compose.yml settings
- [ ] Adjust port ranges if needed
- [ ] Build and start container
  ```bash
  docker-compose up -d
  ```
- [ ] Verify container running
  ```bash
  docker-compose ps
  ```
- [ ] Check logs for errors
  ```bash
  docker-compose logs -f
  ```

### Initial Verification
- [ ] Health check responds
  ```bash
  curl http://localhost:8000/api/health
  ```
- [ ] Web UI accessible
  ```
  Open: http://your-server-ip:8000
  ```
- [ ] API returns empty channel list
  ```bash
  curl http://localhost:8000/api/channels
  ```

## Configuration

### First Channel Setup
- [ ] Open web dashboard
- [ ] Create test channel
  - [ ] Name: Test Channel
  - [ ] RTP IP: Your server IP
  - [ ] RTP Port: 5000
- [ ] Channel created successfully
- [ ] Channel appears in dashboard

### MediaLive Configuration
- [ ] MediaLive output group configured as UDP/RTP
- [ ] Primary destination set: `rtp://your-server-ip:5000`
- [ ] Backup destination set (optional): `rtp://your-server-ip:5001`
- [ ] SCTE-35 passthrough enabled
- [ ] Container format: MPEG-TS
- [ ] Video/audio codecs configured
- [ ] MediaLive channel started

### Output Configuration
- [ ] Test output added
  - [ ] Protocol selected (SRT or RTMP)
  - [ ] URL configured correctly
  - [ ] Name assigned
- [ ] Output appears in dashboard
- [ ] Output status visible

### Go Live Test
- [ ] Start distributor channel (click "Start")
- [ ] Channel status changes to "running"
- [ ] Outputs show "running" status
- [ ] Verify stream at destination
- [ ] Check uptime counter increments
- [ ] No errors in dashboard

## Post-Deployment

### Monitoring Setup
- [ ] Bookmark dashboard URL
- [ ] Test WebSocket real-time updates
- [ ] Verify error messages appear (test with bad URL)
- [ ] Check log rotation configured
  ```bash
  docker-compose logs --tail=100
  ```

### Documentation
- [ ] Save configuration backup
  ```bash
  cp -r config config-backup-$(date +%Y%m%d)
  ```
- [ ] Document channel IDs and purposes
- [ ] Document output destinations
- [ ] Create runbook for operators
- [ ] Share dashboard URL with team

### Performance Validation
- [ ] Monitor CPU usage
  ```bash
  docker stats medialive-distributor
  ```
- [ ] Check memory consumption
- [ ] Verify network bandwidth usage
  ```bash
  iftop -i eth0
  ```
- [ ] Confirm low latency (<500ms end-to-end)

### Security Hardening (if exposed)
- [ ] Set up reverse proxy (nginx/Apache)
- [ ] Configure HTTPS with SSL certificate
- [ ] Add authentication (basic auth or OAuth)
- [ ] Restrict firewall to known IPs only
- [ ] Review security groups

### Backup Configuration
- [ ] Automated backup script created
  ```bash
  cp /opt/backup-script.sh /opt/medialive-distributor/
  chmod +x /opt/medialive-distributor/backup-script.sh
  ```
- [ ] Cron job scheduled
  ```bash
  crontab -e
  # Add: 0 2 * * * /opt/medialive-distributor/backup-script.sh
  ```
- [ ] Test backup restoration process

## Production Readiness

### Functional Tests
- [ ] Create channel via API
- [ ] Add output via API
- [ ] Start/stop channel
- [ ] Remove output without interruption
- [ ] Delete channel
- [ ] Run test suite
  ```bash
  ./test.sh
  ```

### Load Tests
- [ ] Create 5 channels simultaneously
- [ ] Add 3-5 outputs per channel
- [ ] Monitor system resources
- [ ] Verify all streams working
- [ ] Test hot-reload (add output during streaming)

### Failure Tests
- [ ] Stop MediaLive, verify error handling
- [ ] Use invalid output URL, check error message
- [ ] Fill disk, verify graceful degradation
- [ ] Kill FFmpeg process, verify recovery
- [ ] Test container restart
  ```bash
  docker-compose restart
  ```

### Documentation Complete
- [ ] README.md reviewed
- [ ] QUICKSTART.md accessible to operators
- [ ] DEPLOYMENT.md reviewed by ops team
- [ ] EXAMPLES.md bookmarked for reference
- [ ] Runbook created for common tasks

## Handoff

### Team Training
- [ ] Operators trained on web dashboard
- [ ] API documentation shared with developers
- [ ] Troubleshooting guide reviewed
- [ ] Emergency contacts documented
- [ ] Escalation procedures defined

### Knowledge Transfer
- [ ] Architecture explained
- [ ] Configuration files location documented
- [ ] Backup/restore procedure demonstrated
- [ ] Log locations identified
- [ ] Monitoring approach established

### Support Resources
- [ ] Documentation links shared
- [ ] GitHub/repository access granted (if applicable)
- [ ] Support contact information provided
- [ ] FAQ created from common questions

## Sign-Off

### Project Completion
- [ ] All checklist items complete
- [ ] System running stable for 24+ hours
- [ ] No critical issues outstanding
- [ ] Performance meets requirements
- [ ] Team confident in operation

### Production Approval
- [ ] Technical lead approval: _________________ Date: _______
- [ ] Operations approval: _________________ Date: _______
- [ ] Project owner approval: _________________ Date: _______

---

## Quick Reference

**Start Application:**
```bash
docker-compose up -d
```

**Stop Application:**
```bash
docker-compose down
```

**View Logs:**
```bash
docker-compose logs -f
```

**Restart Application:**
```bash
docker-compose restart
```

**Check Health:**
```bash
curl http://localhost:8000/api/health
```

**Backup Configuration:**
```bash
tar -czf config-backup.tar.gz config/
```

**Dashboard URL:**
```
http://your-server-ip:8000
```

---

**Checklist Version:** 1.0  
**Last Updated:** 2025-10-30  
**Status:** ☐ In Progress  ☐ Complete  ☐ Production
