# Stage 1: Build Stage
FROM node:18-alpine AS builder

# Set working directory
WORKDIR /app

# Copy package.json and lock file (detect pnpm-lock.yaml or package-lock.json)
COPY package.json ./
COPY package-lock.json* pnpm-lock.yaml* ./

# Install pnpm if pnpm-lock.yaml exists, otherwise use npm
RUN if [ -f pnpm-lock.yaml ]; then \
      npm install -g pnpm && pnpm install --frozen-lockfile; \
    elif [ -f package-lock.json ]; then \
      npm ci; \
    else \
      echo "Lockfile not found." && exit 1; \
    fi

# Copy the rest of the application code
COPY . .

# Set NEXT_TELEMETRY_DISABLED to 1 to disable telemetry during build
ENV NEXT_TELEMETRY_DISABLED 1

# Build the Next.js application
RUN if [ -f pnpm-lock.yaml ]; then \
      pnpm build; \
    else \
      npm run build; \
    fi

# Stage 2: Production Stage
FROM node:18-alpine

WORKDIR /app

# Set NEXT_TELEMETRY_DISABLED to 1 to disable telemetry
ENV NODE_ENV production
ENV NEXT_TELEMETRY_DISABLED 1

# Create a non-root user for security
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Copy necessary files from the builder stage
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json

# Change ownership of the app directory
# USER nextjs
# Temporarily commenting out USER change as it might cause permission issues 
# with port binding or file system access in some environments without further config.
# Re-enable and test thoroughly if stricter security is needed.

EXPOSE 3000

# Set the correct command to start the production server
# Use pnpm start if pnpm-lock.yaml exists
CMD if [ -f pnpm-lock.yaml ]; then \
      pnpm start; \
    else \
      npm start; \
    fi 