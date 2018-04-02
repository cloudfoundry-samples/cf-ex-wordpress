## CloudFoundry PHP Example Application:  Wordpress

This is an example application which can be run on CloudFoundry using the [PHP Build Pack].

This is an out-of-the-box implementation of Wordpress.  It's an example of how common PHP applications can easily be run on CloudFoundry.

### Usage w/Volume Services

1. Download latest Wordpress files: `curl -L -o wordpress-latest.zip https://wordpress.org/latest.zip`
2. Extract them: `unzip wordpress-latest.zip && rm wordpress-latest.zip`
3. Create `manifest.yml` with the contents:

   ```
   ---
   applications:
   - name: wordpress
     memory: 128M
     path: .
     route: wordpress-on.<app-domain>
     buildpack: php_buildpack
     services:
     - wordpress-mysql-db
   ```

4. Create your MySQL DB.  You can use any MySQL DB that you like, just make sure that the service name matches the service name in `manifest.yml` from step #2.  

   Example using Pivotal MySQL v1: `cf create-service p-mysql 100mb wordpress-mysql-db`.

5. Create your persistent store.  This can be any volume services implementation.

   Example using NFS:  `cf create-service nfs Existing wordpress-files -c '{"share": "<nfs-server>/path/to/nfs/files"}'``
   
   The files stored under `wp-content` (themes, plugins, media, etc..) will be created under this mount.

6. Run `mv wordpress/wp-config-sample.php wordpress/wp-config.php`.
7. Now edit `wordpress/wp-config.php`, replace the database config lines with the following:

    ```
    // ** Read MySQL service properties from _ENV['VCAP_SERVICES']
    $services = json_decode($_ENV['VCAP_SERVICES'], true);
    $service = $services['p-mysql'][0];  // pick the first MySQL service

    // ** MySQL settings - You can get this info from your web host ** //
    /** The name of the database for WordPress */
    define('DB_NAME', $service['credentials']['name']);

    /** MySQL database username */
    define('DB_USER', $service['credentials']['username']);

    /** MySQL database password */
    define('DB_PASSWORD', $service['credentials']['password']);

    /** MySQL hostname */
    define('DB_HOST', $service['credentials']['hostname'] . ':' . $service['credentials']['port']);

    /** Database Charset to use in creating database tables. */
    define('DB_CHARSET', 'utf8');

    /** The Database Collate type. Don't change this if in doubt. */
    define('DB_COLLATE', '');
    ```

    Make sure that the key used to look up the service (i.e. `p-mysql` above) matches the key used by your MySQL service provider.  You can see this if you run `cf env <app>` with a bound MySQL instance.

8. Configure the remainder of `wp-config.php` as you normally would for a new Wordpress site.
9. Add extensions files `.bp-config/php/php.ini.d/wp-extensions.ini`

    ```
    extension=mbstring.so
    extension=mysqli.so
    extension=gd.so
    extension=zip.so
    extension=openssl.so
    extension=sockets.so
    ```

10. Create the file `.bp-config/options.json` and edit it.  Add the following:

    ```
    {
        "WEBDIR": "wordpress",
        "PHP_VERSION": "{PHP_71_LATEST}"
    }
    ```

You can use `PHP_70_LATEST` for the latest PHP 7.0 version or `PHP_72_LATEST` for the latest PHP 7.2 version.

11. Run `mv wordpress/wp-content wordpress/wp-content-orig` (name of new folder *must* be exactly as show here).  We save the original contents to seed our persistent storage.  If the persistent storage has files, then the originals are simply removed (see `.profile` script).
12. Create the file `.profile` and add the following:

    ```
    #!/bin/bash

    # set path of where NFS partition is mounted
    MOUNT_FOLDER="/home/vcap/app/files"

    # set name of folder in which to store files on the NFS partition
    WPCONTENT_FOLDER="$(echo $VCAP_APPLICATION | jq -r .application_name)"

    # Does the WPCONTENT_FOLDER exist under MOUNT_FOLDER?  If not seed it.
    TARGET="$MOUNT_FOLDER/$WPCONTENT_FOLDER"
    if [ ! -d "$TARGET" ]; then
        echo "First run, moving default Wordpress files to the remote volume"
        mv "/home/vcap/app/wordpress/wp-content-orig" "$TARGET"
        ln -s "$TARGET" "/home/vcap/app/wordpress/wp-content"

        # Write warning to remote folder
        echo "!! WARNING !! DO NOT EDIT FILES IN THIS DIRECTORY!!" > \
            "$TARGET/WARNING_DO_NOT_EDIT_THIS_DIRECTORY"
    else
        ln -s "$TARGET" "/home/vcap/app/wordpress/wp-content"
        rm -rf "/home/vcap/app/wordpress/wp-content-orig"  # we don't need this
    fi
    ```

    You can edit `MOUNT_FOLDER` and `WPCONTENT_FOLDER`, but you don't need to as long as you follow the rest of the instructions.  If you need/want to edit, `MOUNT_FOLDER` must match the `mount` location in step #14.  The `WPCONTENT_FOLDER` can be named anything, and will default to your application name.

13. Run `cf push --no-start`.  The `--no-start` option is critical as we need to bind our volume service before we actually start the app (see step #14).
14. Bind your volume services instance to the app.

    Example using NFS:  `cf bind-service wordpress wordpress-files -c '{"uid": "1001", "gid": "1001", "mount": "/home/vcap/app/files"}'`
    
    We cannot do this in `manifest.yml` as we need to specify custom properties for NFS.  Note that `mount` must match the value of `MOUNT_FOLDER` from step #12 and your `.profile` file.  
    
    In the case of NFS, don't forget to adjust the `uid` and `gid` so they match the uid/gid on your user on the NFS server.  You'll get permissions errors if they don't match.
15. Run `cf start wordpress`.
16. Open your URL in the browser and configure Wordpress as you normally would.

### Persistent Storage

If you've ever used Wordpress before, you're probably familiar with the way that you can install new themes and plugins through the WebUI.  This and other actions like uploading media files work by allowing the Wordpress application itself to modify files on your local disk.  Unfortunatley, this is going to cause [a problem](#caution) when you deploy to CloudFoundry.

A naive approach to solving this problem is to simply bundle these files, themes, plugins and media, with your application.  That way when you `cf push`, the files will continue to exist.  There are multiple problems with this approach, like large and possibly slow uploads, tracking what's changed by actions in Wordpress and the fact that you probably don't want to push every time you need to upload media.  Given this, it's likely that for any serious installation of Wordpress you want a better solution.

One good solution is to use one of the third party plugins for Wordpress which allow you to upload media files to a storage system like Amazon's S3.  Your media is then safely stored outside of your application.  The final bit for using this solution is to install your themes & plugins locally, using a tool like [wp-cli](https://wp-cli.org/) or a local staging server, then push the themes and plugins up with your application.  This can still be a bit slow if you have lots of plugins, but it's better than the naive approach as media is not being uploaded.

The solution that's documented in this guide is to use Volume Services.  This is a mechanism in CF which allows you to attach a persistent volume to your application.  The instructions above walk you would mounting the persistent volume in place of your `wp-content` folder, which puts media, themes and plugins all onto the persistent disk.  This is a convenient solution because you can use Wordpress to manage media, themes and plugins and files will all be safe.

### Caution

Please read the following before using Wordpress in production on CloudFoundry.

1. Wordpress is designed to write to the local file system.  This does not work well with CloudFoundry, as an application's [local storage on CloudFoundry] is ephemeral.  In other words, Wordpress will write things to the local disk and they will eventually disappear.  See the [Persistent Storage](#persistent-storage) above for ways to work around this.

1. This is not an issue with Wordpress specifically, but PHP stores session information to the local disk.  As mentioned previously, the local disk for an application on CloudFoundry is ephemeral, so it is possible for you to lose session and session data.  If you need reliable session storage, look at storing session data in an SQL database or with a NoSQL service.

### License

This project is licensed under the Apache v2 license.


[PHP Build Pack]:https://github.com/dmikusa-pivotal/cf-php-build-pack
[secret keys]:https://github.com/dmikusa-pivotal/cf-ex-worpress/blob/master/wp-config.php#L49
[WordPress.org secret-key service]:https://api.wordpress.org/secret-key/1.1/salt
[ClearDb]:https://www.cleardb.com/
[local storage on CloudFoundry]:http://docs.cloudfoundry.org/devguide/deploy-apps/prepare-to-deploy.html#filesystem
[wp-content directory]:http://codex.wordpress.org/Determining_Plugin_and_Content_Directories
[ephemeral file system]:http://docs.cloudfoundry.org/devguide/deploy-apps/prepare-to-deploy.html#filesystem

