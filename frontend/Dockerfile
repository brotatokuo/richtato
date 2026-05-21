FROM node:20-alpine

# Set working directory
WORKDIR /app

# Match packageManager in package.json (Yarn Berry)
RUN corepack enable

# Copy package files
COPY package.json yarn.lock .yarnrc.yml ./

# Install dependencies
RUN yarn install --immutable

# Copy source code
COPY . .

# Expose port
EXPOSE 3000

# Start development server
CMD ["yarn", "dev", "--host", "0.0.0.0"]
