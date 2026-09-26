.PHONY: help docker servers stop restart clean dev dev-stop

.DEFAULT_GOAL := help

help:
	@echo "SpecIdol Makefile commands:"
	@echo ""
	@echo "Docker commands:"
	@echo "  make docker      Build Docker image"
	@echo "  make servers     Run Docker container (port 80 + 8765)"
	@echo "  make stop        Stop and remove Docker container"
	@echo "  make restart     Stop, rebuild, and restart container"
	@echo "  make clean       Stop container, remove container and image"
	@echo ""
	@echo "Local development commands:"
	@echo "  make dev         Run without Docker (port 80 + 8765, needs sudo)"
	@echo "  make dev-stop    Stop local dev servers"
	@echo ""
	@echo "Quick start:"
	@echo "  make docker && make servers"
	@echo "  Then visit http://localhost"

# Docker commands (default)
docker:
	docker build -t specidol .

servers:
	docker run -d --name specidol -p 80:80 -p 8765:8765 specidol
	@echo ""
	@echo "Servers running:"
	@echo "  - Web interface: http://localhost"
	@echo "  - WebSocket relay: ws://localhost:8765"
	@echo ""
	@echo "Run 'make stop' to stop servers"
	@echo "Run 'docker logs -f specidol' to view logs"

stop:
	docker stop specidol 2>/dev/null || true
	docker rm specidol 2>/dev/null || true

restart: stop docker servers

clean:
	docker stop specidol 2>/dev/null || true
	docker rm specidol 2>/dev/null || true
	docker rmi specidol 2>/dev/null || true
	@echo "Cleaned up specidol container and image"

# Local development (without Docker)
dev:
	@echo "Starting WebSocket relay server on port 8765..."
	@python3 server/relay.py & echo $$! > .relay.pid
	@echo "Starting HTTP server on port 80..."
	@python3 -m http.server 80 --directory www & echo $$! > .http.pid
	@echo ""
	@echo "Servers running:"
	@echo "  - WebSocket relay: ws://localhost:8765"
	@echo "  - HTTP server: http://localhost"
	@echo ""
	@echo "Run 'make dev-stop' to stop servers"
	@wait

dev-stop:
	@if [ -f .relay.pid ]; then \
		kill `cat .relay.pid` 2>/dev/null || true; \
		rm .relay.pid; \
		echo "Stopped WebSocket relay server"; \
	fi
	@if [ -f .http.pid ]; then \
		kill `cat .http.pid` 2>/dev/null || true; \
		rm .http.pid; \
		echo "Stopped HTTP server"; \
	fi
	@lsof -ti :8765 | xargs kill -9 2>/dev/null || true
	@lsof -ti :80 | xargs kill -9 2>/dev/null || true
