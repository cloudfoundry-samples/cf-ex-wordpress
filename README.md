CloudFoundry PHP example application:  Wordpress
================================================

This is an example application which can be run on Cloudfoundry using the [PHP Buildpack](https://github.com/dmikusa-pivotal/cf-php-apache-buildpack.git).

This is an out-of-the-box implementation of Wordpress 3.5.2.  It's an example of how common PHP applications can easily be run on CloudFoundry.

Usage
-----

Clone the app and push it to CloudFoundry.

```
git clone https://github.com/dmikusa-pivotal/cf-ex-worpress
cd cf-ex-wordpress
cf push --buildpack=https://github.com/dmikusa-pivotal/cf-php-apache-buildpack.git
```

Changes
-------

These changes were made to prepare Wordpress to run on CloudFoundry.

1. Edit ```wp-config.php```, configure to use CloudFoundry database.  Here's a [link]() to the change.
2. Enabled mod_rewrite
3. Added a custom php.ini file, not strictly necessary though.

