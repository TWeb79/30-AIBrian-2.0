# BRAIN 2.0 Frontend - Dockerfile
# Production build with Nginx - supports both React build and standalone brain2_ui.jsx

# ─────────────────────────────────────────────────────────────────────────────
# Build Stage (for React app)
# ─────────────────────────────────────────────────────────────────────────────
FROM node:20-alpine AS build

WORKDIR /app

# Copy package files
COPY package.json ./

# Install dependencies
RUN npm install

# Copy source files
COPY src ./src
COPY index.html ./

# Build the app
RUN npm run build

# ─────────────────────────────────────────────────────────────────────────────
# Production Stage
# ─────────────────────────────────────────────────────────────────────────────
FROM nginx:alpine AS production

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built React files from build stage
COPY --from=build /app/dist /usr/share/nginx/html

# ALSO copy brain2_ui.jsx as standalone app (root level)
COPY brain2_ui.jsx /usr/share/nginx/html/brain2_ui.jsx

# Create standalone HTML wrapper for brain2_ui.jsx
RUN echo '<!DOCTYPE html>\
<html lang="en">\
<head>\
  <meta charset="UTF-8">\
  <meta name="viewport" content="width=device-width, initial-scale=1.0">\
  <title>BRAIN 2.0 - OSCEN Neural Interface</title>\
  <link rel="preconnect" href="https://fonts.googleapis.com">\
  <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700;800&display=swap" rel="stylesheet">\
  <style>\
    * { margin: 0; padding: 0; box-sizing: border-box; }\
    html, body, #root { height: 100%; width: 100%; overflow: hidden; }\
    body { font-family: "JetBrains Mono", monospace; background: #02060e; }\
  </style>\
</head>\
<body>\
  <div id="root"></div>\
  <script src="https://unpkg.com/react@18/umd/react.production.min.js" crossorigin></script>\
  <script src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js" crossorigin></script>\
  <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>\
  <script type="text/babel" src="/brain2_ui.jsx"></script>\
</body>\
</html>' > /usr/share/nginx/html/index-brain2.html

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost/health || exit 1

CMD ["nginx", "-g", "daemon off;"]
