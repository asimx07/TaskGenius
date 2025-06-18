# Stage 1: Install dependencies and build the Next.js application
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package.json and package-lock.json to leverage Docker cache
COPY package.json package-lock.json ./

# Install dependencies
RUN npm install

# Copy the rest of the frontend application
COPY . .

# Build the Next.js application
RUN npm run build

# Stage 2: Serve the Next.js application with a lightweight server
FROM node:20-alpine AS runner

WORKDIR /app

# Set environment variables for production
ENV NODE_ENV production

# Copy necessary files from the builder stage
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json

# Expose the port Next.js runs on
EXPOSE 3000

# Command to run the Next.js application
CMD ["npm", "start"]
