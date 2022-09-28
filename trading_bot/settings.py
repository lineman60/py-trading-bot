### Setting of the trading bot ###

SUMMER_TIME_US=True
SUMMER_TIME_EUROPE=True

## IB configuration
IB_LOCALHOST='127.0.0.1'
IB_PORT=7496

## Preselection to be used for the different stock exchanges ##
# possible values out-of-the-box:
# "retard","macd_vol","divergence", "wq7","wq31","wq53","wq54", "realmadrid"
DIC_PRESEL={
    "Paris":["retard_manual","wq7","wq54"],
    "XETRA":["retard_manual","wq7","wq53"], 
    "Nasdaq":["retard","wq31","wq53"],
    #"NYSE":["retard"]
    }

DIC_PRESEL_SECTOR={
    "realestate":["retard"],
    "industry":[],
    "it":["retard"],
    "com":[],
    "staples":[],
    "consumer":[],
    "utilities":[],
    "energy":[],
    "fin":[],
    "materials":[],
    "healthcare":[],
    }

## Configuration of Telegram ##
PF_CHECK=True
INDEX_CHECK=True
REPORT_17h=True #for Paris and XETRA
REPORT_22h=True
HEARTBEAT=False # to test telegram

ALERT_THRESHOLD=3 #in %
ALARM_THRESHOLD=5 #in %
ALERT_HYST=1 #margin to avoid alert/recovery at high frequency

## Order settings ##
USE_IB_FOR_DATA=False #use IB for Data or YF
TIME_INTERVAL_CHECK=10 #in minutes, interval between two checks of pf values

PERFORM_ORDER=False #test or use IB to perform orders
## Can be configured for each strategy separately (depending on how often the strategy will trade)
## relation is PERFORM_ORDER and DIC_PERFORM_ORDER
DIC_PERFORM_ORDER={
    "normal":True,
    "normal_index":False,
    "macd_vol":True,
    "retard":True,
    "retard_manual":False,
    "wq7":False,
    "wq31":False,
    "wq53":False,
    "wq54":False,
    "divergence":False
    }

## Configuration of the strategies ##
# Frequency is the number of days between successive candidates actualisation

DIVERGENCE_MACRO=True
RETARD_MACRO=True

DAILY_REPORT_PERIOD=3 #in year

VOL_MAX_CANDIDATES_NB=1
MACD_VOL_MAX_CANDIDATES_NB=1
HIST_VOL_MAX_CANDIDATES_NB=1
DIVERGENCE_THRESHOLD=0.005
VOL_SLOW_FREQUENCY=10
VOL_SLOW_MAX_CANDIDATES_NB=2
MACD_VOL_SLOW_FREQUENCY=10
MACD_VOL_SLOW_MAX_CANDIDATES_NB=2
HIST_VOL_SLOW_FREQUENCY=10
HIST_VOL_SLOW_MAX_CANDIDATES_NB=2
REALMADRID_DISTANCE=400
REALMADRID_FREQUENCY=30
REALMADRID_MAX_CANDIDATES_NB=2
RETARD_MAX_HOLD_DURATION=15

STOCH_LL=20
STOCH_LU=80
BBAND_THRESHOLD=0.15

#for some major events, that cannot be detected only with technical analysis
FORCE_MACRO_TO="bear" #"bull"/"uncertain"/""


"""
Django settings for trading_bot project.

Generated by 'django-admin startproject' using Django 3.2.8.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.2/ref/settings/
"""

### Configuration Django
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

if DEBUG:
    with open('trading_bot/etc/DJANGO_SECRET') as f:
        SECRET_KEY = f.read().strip()
    with open('trading_bot/etc/DB_SECRET') as f:
        DB_SECRET_KEY = f.read().strip()
    with open('trading_bot/etc/DB_USER') as f:
        DB_USER = f.read().strip()
else:
    SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY') 

ALLOWED_HOSTS = []

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'reporting.apps.ReportingConfig',
    'orders.apps.OrdersConfig',
    'django_filters'
    
]

MIDDLEWARE = [
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'trading_bot.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'trading_bot.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

#if DEBUG:
DATABASES = {
'default': {
     'ENGINE': 'django.db.backends.postgresql',
     'NAME': 'pgtradingbotdb',
     'USER': DB_USER,
     'PASSWORD': DB_SECRET_KEY,
     'HOST': 'localhost',
     'PORT': '',
 }
}

REDIS_PASSWORD=""

#if DEBUG:
REDIS_HOST="localhost"
REDIS_PORT="6379"
REDIS_DB=0

REDIS_URL = ':%s@%s:%s/%d' % (
        REDIS_PASSWORD,
        REDIS_HOST,
        REDIS_PORT,
        REDIS_DB)

CELERY_BROKER_URL = 'redis://'+REDIS_URL 

# CELERY
if not DEBUG:
    CELERY_BROKER_POOL_LIMIT= 1
    CELERY_BROKER_HEARTBEAT = None # We're using TCP keep-alive instead
    CELERY_BROKER_CONNECTION_TIMEOUT = 120 # May require a long timeout due to Linux DNS timeouts etc
    CELERY_RESULT_BACKEND = None 
    CELERY_WORKER_PREFETCH_MULTIPLIER = 1
#CELERY_RESULT_BACKEND = 'pyamqp://guest@localhost//'
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.9/howto/static-files/
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATIC_URL = '/static/'

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

if DEBUG:
    URL_ROOT= 'http://localhost:8000' 
else:
    URL_ROOT='https://tradingbot.herokuapp.com'

#?Celery
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'