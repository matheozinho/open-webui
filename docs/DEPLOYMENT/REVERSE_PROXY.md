# Reverse Proxy Configuration

This guide covers setting up reverse proxies for Open WebUI and Ollama, allowing you to host the UI and models separately while retaining RAG and RBAC features.

## Apache Configuration

### Open WebUI Reverse Proxy

For the UI configuration, you can set up the Apache VirtualHost as follows:

```
# Assuming you have a website hosting this UI at "server.com"
<VirtualHost 192.168.1.100:80>
    ServerName server.com
    DocumentRoot /home/server/public_html

    ProxyPass / http://server.com:3000/ nocanon
    ProxyPassReverse / http://server.com:3000/
    # Needed after 0.5
    ProxyPass / ws://server.com:3000/ nocanon
    ProxyPassReverse / ws://server.com:3000/

</VirtualHost>
```

Enable the site first before you can request SSL:

`a2ensite server.com.conf` # this will enable the site. a2ensite is short for "Apache 2 Enable Site"

### SSL Configuration for Open WebUI

```
# For SSL
<VirtualHost 192.168.1.100:443>
    ServerName server.com
    DocumentRoot /home/server/public_html

    ProxyPass / http://server.com:3000/ nocanon
    ProxyPassReverse / http://server.com:3000/
    # Needed after 0.5
    ProxyPass / ws://server.com:3000/ nocanon
    ProxyPassReverse / ws://server.com:3000/

    SSLEngine on
    SSLCertificateFile /etc/ssl/virtualmin/170514456861234/ssl.cert
    SSLCertificateKeyFile /etc/ssl/virtualmin/170514456861234/ssl.key
    SSLProtocol all -SSLv2 -SSLv3 -TLSv1 -TLSv1.1

    SSLProxyEngine on
    SSLCACertificateFile /etc/ssl/virtualmin/170514456865864/ssl.ca
</VirtualHost>
```

### Prerequisites for SSL

Run the following commands:

`snap install certbot --classic`
`snap apt install python3-certbot-apache` (this will install the apache plugin).

Navigate to the apache sites-available directory:

`cd /etc/apache2/sites-available/`

Create server.com.conf if it is not yet already created, containing the above `<virtualhost>` configuration (it should match your case. Modify as necessary). Use the one without the SSL:

Once it's created, run `certbot --apache -d server.com`, this will request and add/create an SSL keys for you as well as create the server.com.le-ssl.conf

## Nginx Configuration

### Open WebUI Reverse Proxy

```
server {
    listen 80;
    server_name server.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}
```

### SSL Configuration for Open WebUI with Nginx

```
server {
    listen 443 ssl http2;
    server_name server.com;

    ssl_certificate /etc/letsencrypt/live/server.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/server.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}
```

## Ollama Server Configuration

On your latest installation of Ollama, make sure that you have setup your api server from the official Ollama reference:

[Ollama FAQ](https://github.com/jmorganca/ollama/blob/main/docs/faq.md)

### TL;DR

The guide doesn't seem to match the current updated service file on linux. So, we will address it here:

Unless when you're compiling Ollama from source, installing with the standard install `curl https://ollama.com/install.sh | sh` creates a file called `ollama.service` in /etc/systemd/system. You can use nano to edit the file:

```
sudo nano /etc/systemd/system/ollama.service
```

Add the following lines:

```
Environment="OLLAMA_HOST=0.0.0.0:11434" # this line is mandatory. You can also specify
```

For instance:

```
[Unit]
Description=Ollama Service
After=network-online.target

[Service]
ExecStart=/usr/local/bin/ollama serve
Environment="OLLAMA_HOST=0.0.0.0:11434" # this line is mandatory. You can also specify 192.168.254.109:DIFFERENT_PORT, format
Environment="OLLAMA_ORIGINS=http://192.168.254.106:11434,https://models.server.city" # this line is optional
User=ollama
Group=ollama
Restart=always
RestartSec=3
Environment="PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games:/s>

[Install]
WantedBy=default.target
```

Save the file by pressing CTRL+S, then press CTRL+X

When your computer restarts, the Ollama server will now be listening on the IP:PORT you specified, in this case 0.0.0.0:11434, or 192.168.254.106:11434 (whatever your local IP address is). Make sure that your router is correctly configured to serve pages from that local IP by forwarding 11434 to your local IP server.

## Ollama Model Reverse Proxy

### Apache Configuration for Ollama

Navigate to the apache sites-available directory:

`cd /etc/apache2/sites-available/`

`nano models.server.city.conf` # match this with your ollama server domain

Add the following virtualhost containing this example (modify as needed):

```

# Assuming you have a website hosting this UI at "models.server.city"
<IfModule mod_ssl.c>
    <VirtualHost 192.168.254.109:443>
        DocumentRoot "/var/www/html/"
        ServerName models.server.city
        <Directory "/var/www/html/">
            Options None
            Require all granted
        </Directory>

        ProxyRequests Off
        ProxyPreserveHost On
        ProxyAddHeaders On
        SSLProxyEngine on

        ProxyPass / http://server.city:1000/ nocanon # or port 11434
        ProxyPassReverse / http://server.city:1000/ # or port 11434

        SSLCertificateFile /etc/letsencrypt/live/models.server.city/fullchain.pem
        SSLCertificateKeyFile /etc/letsencrypt/live/models.server.city/privkey.pem
        Include /etc/letsencrypt/options-ssl-apache.conf
    </VirtualHost>
</IfModule>
```

You may need to enable the site first (if you haven't done so yet) before you can request SSL:

`a2ensite models.server.city.conf`

#### For the SSL part of Ollama server

Run the following commands:

Navigate to the apache sites-available directory:

`cd /etc/apache2/sites-available/`
`certbot --apache -d server.com`

```
<VirtualHost 192.168.254.109:80>
    DocumentRoot "/var/www/html/"
    ServerName models.server.city
    <Directory "/var/www/html/">
        Options None
        Require all granted
    </Directory>

    ProxyRequests Off
    ProxyPreserveHost On
    ProxyAddHeaders On
    SSLProxyEngine on

    ProxyPass / http://server.city:1000/ nocanon # or port 11434
    ProxyPassReverse / http://server.city:1000/ # or port 11434

    RewriteEngine on
    RewriteCond %{SERVER_NAME} =models.server.city
    RewriteRule ^ https://%{SERVER_NAME}%{REQUEST_URI} [END,NE,R=permanent]
</VirtualHost>

```

### Nginx Configuration for Ollama

```
server {
    listen 80;
    server_name models.server.city;

    location / {
        proxy_pass http://localhost:11434;  # or your Ollama port
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}
```

Don't forget to restart/reload your web server:

- Apache: `systemctl reload apache2`
- Nginx: `systemctl reload nginx`

Open your site at https://server.com!

**Congratulations**, your _**Open-AI-like Chat-GPT style UI**_ is now serving AI with RAG, RBAC and multimodal features! Download Ollama models if you haven't yet done so!

If you encounter any misconfiguration or errors, please file an issue or engage with our discussion. There are a lot of friendly developers here to assist you.