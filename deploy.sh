#!/bin/bash
virtualenv --no-site-packages --distribute .venv
. .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
git submodule add --  https://github.com/stephband/bolt.git hoard/static/bolt
git submodule update --init --recursive
cd hoard
createdb hoard
python manage.py collectstatic --noinput
python manage.py syncdb
mkdir -p ../tmp/media
mkdir /var/tmp/letsencrypt-auto

cd
mkdir -p backup
(crontab -l ; echo "@daily ~/hoard/.venv/bin/python ~/hoard/hoard/manage.py clearsessions") | crontab -
(crontab -l ; echo "@daily pg_dump -f ~/backup/hoard.sql hoard") | crontab -

cd hoard/conf/prod
echo
echo "sudo ln -s $PWD/supervisord.gunicorn.conf /etc/supervisord.d/hoard.conf"
echo "sudo ln -s $PWD/nginx.conf /etc/nginx/sites-enabled/hoard.conf"
echo "sudo supervisorctl update"
echo "sudo service nginx configtest"
echo
cd
