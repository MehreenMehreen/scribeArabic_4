# Instructions on Running This Project

python3 manage.py runserver 0.0.0.0:8000
conda env is sfr_arabic


## Install Django
At the console type:
pip3 install Django

For more see:
[Django official page](https://docs.djangoproject.com/en/4.1/topics/install/#installing-official-release)

# For production put secret key in secret_key.txt

## For celery (optional)
install celery + redis. The project can run with gunicorn and caddy

# For authentication/password "forget password" to work
## For authentication, users can retrieve password via email link, put email and authentication token in 
email_host.txt and email_host_password.txt (see settings.py). (Read Google's docs on how to setup tokens for email)
## Run the server
At the console type:

```
python3 manage.py runserver
```

## Run the client
Open a browser and enter the URL:

```
http://127.0.0.1:8000/login
```

