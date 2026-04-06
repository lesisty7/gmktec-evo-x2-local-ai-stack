FROM mcr.microsoft.com/playwright:v1.50.0-jammy

RUN apt-get update && apt-get install -y socat && rm -rf /var/lib/apt/lists/*

ENV NODE_ENV=production \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

RUN npm install -g @playwright/mcp@latest

WORKDIR /app
EXPOSE 8931

CMD npx -y @playwright/mcp@latest --port 8930 --host 127.0.0.1 --allowed-hosts "*" > /tmp/mcp.log 2>&1 & \
    sleep 3 && \
    echo "--- STARTING PROXY WITH DEBUG LOGGING ---" && \
    socat -v -d -d TCP-LISTEN:8931,fork,bind=0.0.0.0 TCP:127.0.0.1:8930
