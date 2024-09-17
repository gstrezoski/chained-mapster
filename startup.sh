# This is a script to start up
# just use it in the custom startup command field when creating the resource
# For example: ./startup.sh
mkdir ./logs
touch ./logs/debug.log

python manage.py migrate
# We have to start it with Daphne as we need the socket connection capability.
python manage.py collectstatic
daphne -b 0.0.0.0 -p 8000 mapster.asgi:application
