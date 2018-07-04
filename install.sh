apt-get install -y nginx uwsgi uwsgi-plugin-python

mkdir -p /var/log/face

# nginx configuration
touch /var/run/client.sock
cp etc/client.conf /etc/nginx/conf.d/

touch /var/run/server.sock
cp etc/server.conf /etc/nginx/conf.d/

service nginx restart


# uwsgi
uwsgi -i etc/server.ini
uwsgi -i etc/client.ini

cp etc/rc.local /etc/
