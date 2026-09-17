./letsencrypt-auto certonly \
    --email marco@cruncher.ch \
    --fullchain-path /home/projects/hoard/hoard/conf/prod/ssl/fullchain.pem \
    --key-path /home/projects/hoard/hoard/conf/prod/ssl/privkey.pem \
    --webroot -w /home/projects/hoard/hoard/conf/prod/ssl/webroot/ \
    -d hoard.com -d www.hoard.com -d hoard.cruncher.ch
