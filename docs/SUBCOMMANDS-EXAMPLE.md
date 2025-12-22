# Example: Creating and Using Subcommands

## Step 1: Create a new Pfyfile for your domain

Let's create tasks for a fictional "myapp" project:

```bash
cat > Pfyfile.myapp.pf << 'EOF'
# Pfyfile.myapp.pf - Tasks for myapp project

task build
  describe Build the myapp application
  shell echo "Building myapp..."
  shell cargo build --release
end

task test
  describe Run myapp tests
  shell echo "Running tests..."
  shell cargo test
end

task clean
  describe Clean myapp build artifacts
  shell echo "Cleaning..."
  shell cargo clean
end

task dev
  describe Start myapp in development mode
  env PORT=3000
  shell echo "Starting dev server on port $PORT..."
  shell cargo run
end

task deploy
  describe Deploy myapp to production
  env ENV=production
  shell echo "Deploying to $ENV..."
  shell ./deploy.sh
end
EOF
```

## Step 2: Include it in your main Pfyfile.pf

```bash
# Add this line to your Pfyfile.pf
echo "include Pfyfile.myapp.pf" >> Pfyfile.pf
```

## Step 3: Use your new subcommand!

```bash
# List all tasks to see your new subcommand
pf list

# You'll see something like:
# [myapp] From Pfyfile.myapp.pf:
#   myapp-build    - Build the myapp application
#   myapp-test     - Run myapp tests
#   myapp-clean    - Clean myapp build artifacts
#   myapp-dev      - Start myapp in development mode
#   myapp-deploy   - Deploy myapp to production

# Now use the subcommand:
pf myapp build
pf myapp test
pf myapp dev

# Or use tasks directly (both work!):
pf run myapp-build
pf myapp-build
```

## Step 4: Multiple ways to use your tasks

```bash
# Via subcommand
pf myapp build
pf myapp deploy

# Direct task name
pf myapp-build
pf myapp-deploy

# With 'run' command
pf run myapp-build
pf run myapp-deploy

# With parameters
pf myapp dev port=8080
pf myapp deploy env=staging

# With global options
pf --env=prod myapp deploy
pf --hosts=server1,server2 myapp deploy
```

## Complete Example: Web + API + Database

Here's how you might organize a full-stack application:

### Pfyfile.frontend.pf
```text
task build
  describe Build frontend assets
  shell npm run build
end

task dev
  describe Start frontend dev server
  shell npm run dev
end

task test
  describe Run frontend tests
  shell npm test
end
```

### Pfyfile.api.pf
```text
task build
  describe Build API server
  shell cargo build --release
end

task dev
  describe Start API dev server
  shell cargo run
end

task test
  describe Run API tests
  shell cargo test
end
```

### Pfyfile.database.pf
```text
task migrate
  describe Run database migrations
  shell diesel migration run
end

task seed
  describe Seed database with test data
  shell diesel migration run --seed
end

task backup
  describe Backup database
  shell pg_dump myapp > backup.sql
end
```

### Pfyfile.pf (main file)
```text
include Pfyfile.frontend.pf
include Pfyfile.api.pf
include Pfyfile.database.pf

task build-all
  describe Build entire application
  shell echo "Building frontend..."
  # Note: Cannot directly call subcommand tasks from within a task
  # But you can call the actual commands
end
```

### Usage
```bash
# Build everything
pf frontend build
pf api build

# Development workflow
pf database migrate
pf database seed
pf api dev &        # Start API in background
pf frontend dev     # Start frontend (foreground)

# Testing
pf frontend test
pf api test

# Production deployment
pf database backup
pf database migrate
pf api build
pf frontend build
```

This organization makes it crystal clear which component you're working with!
