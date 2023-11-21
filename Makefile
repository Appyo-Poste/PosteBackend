.PHONY: up down clean

up:
	docker compose up --build -d

down:
	docker compose down --remove-orphans

clean:
	docker compose down --remove-orphans --volumes
