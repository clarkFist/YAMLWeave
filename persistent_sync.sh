#!/bin/bash

# 持久化GitHub同步脚本 - 在后台持续尝试直到成功
LOGFILE="sync_attempts.log"
PIDFILE="sync.pid"
REPO_URL="https://github.com/clarkFist/YAMLWeave.git"

# 检查是否已在运行
if [ -f "$PIDFILE" ]; then
    PID=$(cat "$PIDFILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo "Sync script already running with PID: $PID"
        exit 1
    else
        rm "$PIDFILE"
    fi
fi

# 记录当前PID
echo $$ > "$PIDFILE"

echo "$(date): Starting persistent sync to $REPO_URL" | tee -a "$LOGFILE"

# 无限循环直到成功
attempt=1
while true; do
    echo "$(date): === Attempt $attempt ===" | tee -a "$LOGFILE"
    
    # 计算等待时间 (指数退避，最大2小时)
    wait_time=$((5 * (2 ** (attempt % 10))))
    if [ $wait_time -gt 7200 ]; then
        wait_time=7200
    fi
    
    echo "$(date): Waiting $wait_time seconds before attempt..." | tee -a "$LOGFILE"
    sleep $wait_time
    
    # 尝试推送
    echo "$(date): Attempting git push..." | tee -a "$LOGFILE"
    
    if git push -u origin main --ipv4 >> "$LOGFILE" 2>&1; then
        echo "$(date): *** SUCCESS! Repository synchronized successfully ***" | tee -a "$LOGFILE"
        git status | tee -a "$LOGFILE"
        git log --oneline -3 | tee -a "$LOGFILE"
        
        # 清理
        rm "$PIDFILE"
        echo "$(date): Persistent sync completed successfully" | tee -a "$LOGFILE"
        exit 0
    fi
    
    # 如果失败，尝试fetch和merge
    echo "$(date): Push failed, trying fetch first..." | tee -a "$LOGFILE"
    
    if timeout 120 git fetch origin main --ipv4 >> "$LOGFILE" 2>&1; then
        echo "$(date): Fetch successful, attempting merge..." | tee -a "$LOGFILE"
        
        if git merge origin/main --allow-unrelated-histories --no-edit >> "$LOGFILE" 2>&1; then
            echo "$(date): Merge successful, retrying push..." | tee -a "$LOGFILE"
            
            if git push -u origin main --ipv4 >> "$LOGFILE" 2>&1; then
                echo "$(date): *** SUCCESS after merge! Repository synchronized ***" | tee -a "$LOGFILE"
                git status | tee -a "$LOGFILE"
                git log --oneline -3 | tee -a "$LOGFILE"
                
                rm "$PIDFILE"
                echo "$(date): Persistent sync completed successfully after merge" | tee -a "$LOGFILE"
                exit 0
            fi
        fi
    fi
    
    echo "$(date): Attempt $attempt failed" | tee -a "$LOGFILE"
    attempt=$((attempt + 1))
    
    # 每100次尝试后创建新的bundle备份
    if [ $((attempt % 100)) -eq 0 ]; then
        echo "$(date): Creating backup bundle after $attempt attempts..." | tee -a "$LOGFILE"
        git bundle create "yamlweave-backup-$(date +%Y%m%d-%H%M%S).bundle" HEAD main
    fi
done