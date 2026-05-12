# goremote.io deployment notes

## Repository

- Upstream: `https://github.com/ashleyhindle/goremote.io`
- Local path: `/Users/town/Projects/boss/ref/goremote.io`
- Tracked commit: `26727e86708fe4650176a2cca61b520e17367359`
- Status: archived legacy PHP/Silex app

## Runtime profile

Official deployment uses:

- `Vagrantfile` with `ubuntu/trusty64`
- Ansible provisioning for `nginx`, `php-fpm`, `mysql`, `memcache`, `beanstalk`, `geoip`, and `composer`
- PHP-era dependencies including `silex/silex ~1.2`, `twig <2`, `phpunit 4.7`, `gulp 3`, and `bower`

## Verification on 2026-05-12

Source was cloned and inspected. Runtime verification did not complete because this machine lacks the required legacy runtime:

- `php` missing
- `composer` missing
- `vagrant` missing
- Docker CLI exists, but Docker daemon was not running during verification

The current `goremote.io` domain resolves to a sales page, so the original hosted service is not available for comparison.

## Recommended run paths

Official Vagrant path, after installing Vagrant:

```bash
cd /Users/town/Projects/boss/ref/goremote.io
rtk vagrant up
```

Composer container path, after starting Docker daemon:

```bash
rtk docker run --rm -v /Users/town/Projects/boss/ref/goremote.io:/app -w /app composer:1.10 install --no-interaction --prefer-dist --no-progress
```

If running on the host, use PHP 5.6 or a similarly old PHP runtime close to the original PHP 5.5 target:

```bash
cd /Users/town/Projects/boss/ref/goremote.io
rtk composer install
```

The app also needs MySQL, Memcached, Beanstalkd, and schema initialization from `sql/`.

