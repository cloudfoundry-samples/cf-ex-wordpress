## CloudFoundry PHP Example Application:  Wordpress

This is an example application which can be run on CloudFoundry using the [PHP Build Pack].

This is an out-of-the-box implementation of Wordpress 4.0.  It's an example of how common PHP applications can easily be run on CloudFoundry.

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

### Persistent Storage

If you've ever used Wordpress before, you're probably familiar with the way that you can install new themes and plugins through the WebUI.  This and other actions like uploading media files work by allowing the Wordpress application itself to modify files on your local disk.  Unfortunatley, this is going to cause [a problem](#caution) when you deploy to CloudFoundry.

A naive approach to solving this problem is to simply bundle these files, themes, plugins and media, with your application.  That way when you `cf push`, the files will continue to exist.  There are multiple problems with this approach, like large and possibly slow uploads, tracking what's changed by actions in Wordpress and the fact that you probably don't want to push every time you need to upload media.  Given this, it's likely that for any serious installation of Wordpress you want a better solution.

One possible better solution is to use one of the third party plugins for Wordpress which allow you to upload media files to a storage system like Amazon's S3.  While this works great for media files, the plugins that I've seen do not address the issue of installing themes or plugins.  Doing this looks like it would still require you to push all the files up with your application, which can be tricky cause there isn't a good way to manually install a Wordpress plugin or theme.

Enter the latest solution.  As of CF release v183, CF now has support for FUSE enabled.  Given this, it's possible to use FUSE to mount a remote file system that Wordpress can use to store your files.  This solution works by mapping the `wp-content` directory to your persistent, remote file system.  Because this is the directory where Wordpress installs themes, plugins and uploads media; the normal functionality of Wordpress simply works as you would expect.

To enable this support in this sample application, simply set the following environment variables in the `manifest.yml` file of this example.

|      Variable     |   Explanation                                        |
------------------- | -----------------------------------------------------|
|      SSH_HOST     | The user, host name or IP address and port of your SSH server. Ex: `user@my.host.name:2222`.  Required. |
|      SSH_PATH     | The full remote path of the directory to mount into the application file system. Required. |
|    SSH_KEY_NAME   | The name of your SSH key.  The public and private key need to be bundled with your application under the `.ssh` directory.  These are used to authenticate with the remote SSH server. Required. |
|      SSH_OPTS     | List of options passed through to `sshfs`.  Defaults to none.  Optional. |

Example:

```
---
applications:
- name: <app-name>
  memory: 128M
  path: .
  buildpack: https://github.com/dmikusa-pivotal/cf-php-build-pack.git
  services:
  - mysql-db
  env:
    SSH_HOST: user@my-ssh-server.name
    SSH_PATH: /home/sshfs/remote
    SSH_KEY_NAME: sshfs
    SSH_OPTS: '["cache=yes", "kernel_cache", "compression=no", "large_read", "Ciphers=arcfour"]'
```

When the above configuration is specified, the example application will take the information and mount the `SSH_PATH` to the `wp-content` directory of your Wordpress application.  This means that anything in Wordpress that would normally be written to the local file system is actually written to the remote path on the `SSH_HOST` specified.

As with the other solutions, this one is not perfect either.  Here are some things to be aware of with this solution.

   - Because files are being stored on a remote server, performance will be impacted by the bandwidth and latency to that server.  In other words, you want the SSH server to be located as closely as possible (ideally on the same LAN) to your CF installation.

   - Wordpress places some of its PHP files within the `wp-content` directory.  These will be stored to your remote file system as well.  When you push your application, these files (not themes, plugins or media) will be overwritten by the build pack.  The sample application does this to make sure the files are up-to-date in the event that you have changed the version of Wordpress.  

   - If you're familiar with FUSE you'll know that it supports many different types of remote file systems, like Webdav, SSHFS and many others.  In this example application, I've chosen SSHFS because it performs well, is secure and comes pre-installed in the CF environment. You could certainly choose to use a different FUSE module, if you prefer another one.

### Changes

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
+$service = $services['cleardb'][0];  // pick the first MySQL service
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

### Caution

Please read the following before using Wordpress in production on CloudFoundry.

1. Wordpress is designed to write to the local file system.  This does not work well with CloudFoundry, as an application's [local storage on CloudFoundry] is ephemeral.  In other words, Wordpress will write things to the local disk and they will eventually disappear.  See the [Persistent Storage](#persistent-storage) above for ways to work around this.

1. This is not an issue with Wordpress specifically, but PHP stores session information to the local disk.  As mentioned previously, the local disk for an application on CloudFoundry is ephemeral, so it is possible for you to lose session and session data.  If you need reliable session storage, look at storing session data in an SQL database or with a NoSQL service.


[PHP Build Pack]:https://github.com/dmikusa-pivotal/cf-php-build-pack
[secret keys]:https://github.com/dmikusa-pivotal/cf-ex-worpress/blob/master/wp-config.php#L49
[WordPress.org secret-key service]:https://api.wordpress.org/secret-key/1.1/salt
[ClearDb]:https://www.cleardb.com/
[local storage on CloudFoundry]:http://docs.cloudfoundry.org/devguide/deploy-apps/prepare-to-deploy.html#filesystem
[wp-content directory]:http://codex.wordpress.org/Determining_Plugin_and_Content_Directories
[ephemeral file system]:http://docs.cloudfoundry.org/devguide/deploy-apps/prepare-to-deploy.html#filesystem

