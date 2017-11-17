#!/bin/bash
set -ex

export DEBIAN_FRONTEND=noninteractive

apt-get update -qq > /dev/null
apt-get install -yqq --no-install-recommends p7zip-full p7zip-rar pst-utils cpanminus poppler-utils postgresql postgresql-server-dev-all build-essential libmagic python3-dev libxml2-dev libxslt1-dev > /dev/null
cpanm --notest Email::Outlook::Message > /dev/null

virtualenv -p python3 /tmp/venv
source /tmp/venv/bin/activate
cd /mnt/snoop
pip install -r requirements.txt

sudo -u postgres createsuperuser root
createdb snoop

( cd /tmp; git clone https://github.com/hoover/testdata )
( cd /mnt/snoop/snoop/site/settings; cp example_testing.py testing_local.py )

pytest --junit-xml junit.xml
