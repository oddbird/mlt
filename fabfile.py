from fabric.api import *

def deploy():
    local('./manage.py collectstatic --noinput')
    local('epio upload')
