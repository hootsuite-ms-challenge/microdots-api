clean:
	docker stop microdots_neo4j
	docker stop microdots_redis
	docker rm microdots_neo4j
	docker rm microdots_redis

neo4j:
	docker run --name microdots_neo4j -d -e 'NEO4J_AUTH=none' -p 7474:7474 -p 7687:7687 neo4j:3.0

redis:
	docker run --name microdots_redis -d -p 6379:6379 redis:2.8

run:
	python manage.py runserver 0.0.0.0:8001

services: neo4j redis

test:
	python manage.py test
