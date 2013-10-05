# CloudFoundry PHP example application: Wordpress

This is an example application which can be run on Cloudfoundry using the [PHP Buildpack](https://github.com/dmikusa-pivotal/cf-php-apache-buildpack.git).

This is an out-of-the-box implementation of Wordpress 3.6.1.  It's an example of how common PHP applications can easily be run on CloudFoundry.

## Usage

### Clone and use [this repository](https://github.com/dmikusa-pivotal/cf-ex-worpress)

```bash
git clone git@github.com:dmikusa-pivotal/cf-ex-worpress.git cf-ex-wordpress
cd cf-ex-wordpress
```

### Make necessary changes

* Edit `htdocs/wp-config.php` and change the [authentication keys](https://github.com/dmikusa-pivotal/cf-ex-worpress/blob/master/htdocs/wp-config.php#L49).  These should be uniqe for every installation.  You can generate these using the [WordPress.org secret-key service](https://api.wordpress.org/secret-key/1.1/salt).
* Edit `config/options.json` and change the email address to your own email address.

### Push this application to a CloudFoundry server

```bash
# Set the target to tell Cloud Foundry which api to use (this will be different if you are not using an account hosted by Cloud Foundry)
cf target api.pivotal.run.io

# Login
cf login

# Push WordPress to Cloud Foundry server
cf push --buildpack=https://github.com/dmikusa-pivotal/cf-php-apache-buildpack.git
```

## Changes

These changes were made to prepare Wordpress to run on CloudFoundry.

1. Create a working directory (`cf\_wordpress` for example)
1. Download the latest version of WordPress and extract the archive.  This will create a `wordpress` folder.  Move/rename this folder to `cf\_wordpress/htdocs`
1. In the `htdocs` folder, rename the sample wp-config file to `wp-config.php`
1. Edit `wp-config.php`, configure to use CloudFoundry database.

```diff
--- wordpress/wp-config-sample.php	2010-11-01 08:45:11.000000000 -0600
+++ cf-ex-wordpress/htdocs/wp-config.php	2013-10-04 14:07:29.857395078 -0600
@@ -14,18 +14,22 @@
  * @package WordPress
  */
 
+// ** Read MySQL service properties from _ENV['VCAP_SERVICES']
+$services = json_decode($_ENV['VCAP_SERVICES'], true);
+$service = $services['cleardb-n/a'][0];  // pick the first MySQL service
+
 // ** MySQL settings - You can get this info from your web host ** //
 /** The name of the database for WordPress */
-define('DB_NAME', 'database_name_here');
+define('DB_NAME', $service['credentials']['name']);
 
 /** MySQL database username */
-define('DB_USER', 'username_here');
+define('DB_USER', $service['credentials']['username']);
 
 /** MySQL database password */
-define('DB_PASSWORD', 'password_here');
+define('DB_PASSWORD', $service['credentials']['password']);
 
 /** MySQL hostname */
-define('DB_HOST', 'localhost');
+define('DB_HOST', $service['credentials']['hostname'] . ':' . $service['credentials']['port']);
 
 /** Database Charset to use in creating database tables. */
 define('DB_CHARSET', 'utf8');
```

1. Enable mod_rewrite and other Apache modules (see `config/extra/httpd-modules.conf`)
1. Create `config/options.json` to configure the administrator email defined in HTTPD

```json
{
  "ADMIN_EMAIL": "you@yourdomain.com"
}
```

1. Add a custom `config/php.ini` file (optional)
