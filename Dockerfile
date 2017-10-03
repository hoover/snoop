FROM python:3
ENV PYTHONUNBUFFERED 1

RUN set -x \
 && echo 'deb http://deb.debian.org/debian jessie non-free' >> /etc/apt/sources.list \
 && echo 'deb http://deb.debian.org/debian jessie-updates non-free' >> /etc/apt/sources.list \
 && echo 'deb http://security.debian.org jessie/updates non-free' >> /etc/apt/sources.list \
 && apt-get update \
 && apt-get install -y --no-install-recommends p7zip-full p7zip-rar pst-utils cpanminus \
 && cpanm --notest Email::Outlook::Message \
 && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /opt/hoover/snoop
WORKDIR /opt/hoover/snoop

ADD requirements.txt ./
RUN pip install -r requirements.txt

COPY . .

CMD waitress-serve --port 80 snoop.site.wsgi:application
