FROM node:20-slim

SHELL ["/bin/bash", "-c"]

ARG lang
ARG dir

ENV LANG ${lang}
ENV NODE_ENV production

WORKDIR /root/${dir}

# Copy package files
COPY package.json package-lock.json* ./

# Copy source code
COPY tsconfig.json ./
COPY src ./src

# Install dependencies and build app
RUN apt -y update && apt -y upgrade && \
    apt -y install python3 make g++ sqlite3 && \
    npm ci --only=production && \
    apt -y remove python3 make g++ && \
    apt -y autoremove && \
    rm -rf /var/lib/apt/lists/* && \
    npm run build && \
    mkdir -p ./db

USER ncadmin

# Run the bot
CMD ["npm", "start"]