## CloudFoundry PHP Example Application:  Wordpress

This is an example application which can be run on CloudFoundry using the [PHP Build Pack].

This is an out-of-the-box implementation of Wordpress 3.8.1.  It's an example of how common PHP applications can easily be run on CloudFoundry.

### Usage

1. Clone the app (i.e. this repo).

  ```bash
  git clone https://github.com/dmikusa-pivotal/cf-ex-worpress.git cf-ex-wordpress
  cd cf-ex-wordpress
  ```

1.  If you don't have one already, create a MySQL service.  With Pivotal Web Services, the following command will create a free MySQL database through [ClearDb].

  ```bash
  cf create-service cleardb spark my-test-mysql-db
  ```

1. Edit the manifest.yml file.  Change the 'host' attribute to something unique.  Then under "services:" change "mysql-db" to the name of your MySQL service.  This is the name of the service that will be bound to your application and thus used by Wordpress.

1. Like every normal Wordpress install, edit `htdocs/wp-config.php` and change the [secret keys].  These should be uniqe for every installation.  You can generate these using the [WordPress.org secret-key service].

1. Push it to CloudFoundry.

  ```bash
  cf push
  ```

  Access your application URL in the browser.  You'll see the familiar Wordpress install screen.  Setup your password and your all set.

### How It Works

When you push the application here's what happens.

1. The local bits are pushed to your target.  This is small, five files around 25k. It includes the changes we made and a build pack extension for Wordpress.
1. The server downloads the [PHP Build Pack] and runs it.  This installs HTTPD and PHP.
1. The build pack sees the extension that we pushed and runs it.  The extension downloads the stock Wordpress file from their server, unzips it and installs it into the `htdocs` directory.  It then copies the rest of the files that we pushed and replaces the default Wordpress files with them.  In this case, it's just the `wp-config.php` file.
1. At this point, the build pack is done and CF runs our droplet.


## Changes

These changes were made to prepare Wordpress to run on CloudFoundry.

1. Edit `wp-config.php`, configure to use CloudFoundry database.

```diff
--- wp-config-sample.php	2013-10-24 18:58:23.000000000 -0400
+++ wp-config.php	2014-03-05 15:44:23.000000000 -0500
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


[PHP Build Pack]:https://github.com/dmikusa-pivotal/cf-php-build-pack
[secret keys]:https://github.com/dmikusa-pivotal/cf-ex-worpress/blob/master/wp-config.php#L49
[WordPress.org secret-key service]:https://api.wordpress.org/secret-key/1.1/salt
[ClearDb]:https://www.cleardb.com/
