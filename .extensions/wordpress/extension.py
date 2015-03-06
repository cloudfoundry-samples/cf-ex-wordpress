"""WordPress Extension

Downloads, installs and configures WordPress
"""
import os
import json
import os.path
import logging
from build_pack_utils import utils


_log = logging.getLogger('wordpress')


DEFAULTS = utils.FormattedDict({
    'WORDPRESS_VERSION': '4.1.1',  # or 'latest'
    'WORDPRESS_PACKAGE': 'wordpress-{WORDPRESS_VERSION}.tar.gz',
    'WORDPRESS_HASH': '258bda90f618d7af3a2db7f22fc926d1fedb06f4',
    'WORDPRESS_URL': 'https://wordpress.org/{WORDPRESS_PACKAGE}',
})


def merge_defaults(ctx):
    for key, val in DEFAULTS.iteritems():
        if key not in ctx:
            ctx[key] = val


def is_sshfs_enabled(ctx):
    return ('SSH_HOST' in ctx.keys() and
            'SSH_KEY_NAME' in ctx.keys() and
            'SSH_PATH' in ctx.keys())


def process_ssh_opts(ctx):
    if 'SSH_OPTS' in ctx.keys():
        try:
            opts = json.loads(ctx['SSH_OPTS'])
            ctx['SSH_OPTS'] = ["-o %s" % opt for opt in opts]
        except TypeError:
            pass  # ignore failures to parse JSON


def enable_sshfs(ctx):
    cmds = []
    if is_sshfs_enabled(ctx):
        process_ssh_opts(ctx)
        # look for ssh keys that were pushed with app, move out of public
        #  directory and set proper permissions (cf push ruins permissions)
        cmds.append(('mv', '$HOME/%s/.ssh' % ctx['WEBDIR'], '$HOME/'))
        cmds.append(('chmod', '644', '$HOME/.ssh/*'))
        cmds.append(('chmod', '600', '$HOME/.ssh/%s' % ctx['SSH_KEY_NAME']))
        # save WP original files
        cmds.append(('mv',
                     '$HOME/%s/wp-content' % ctx['WEBDIR'],
                     '/tmp/wp-content'))
        # mount sshfs
        cmds.append(('mkdir', '-p', '$HOME/%s/wp-content' % ctx['WEBDIR']))
        cmd = ['sshfs',
               "%s:%s" % (ctx['SSH_HOST'], ctx['SSH_PATH']),
               '$HOME/%s/wp-content' % ctx['WEBDIR'],
               '-o IdentityFile=$HOME/.ssh/%s' % ctx['SSH_KEY_NAME'],
               '-o StrictHostKeyChecking=yes',
               '-o UserKnownHostsFile=$HOME/.ssh/known_hosts',
               '-o idmap=user']
        cmd.extend(ctx['SSH_OPTS'])
        cmds.append(cmd)
        # copy files
        cmds.append(('rsync', '-rtvu',
                     '/tmp/wp-content', '$HOME/%s' % ctx['WEBDIR']))
        # clean up
        cmds.append(('rm', '-rf', '/tmp/wp-content'))
        # we unmount because we want sshfs to be run as a proc
        #  that way if it fails, it will cause the app to fail
        cmds.append(('fusermount',
                     '-u', '$HOME/%s/wp-content' % ctx['WEBDIR']))
    return cmds


def write_sshfs_warning(ctx):
    warning_file = os.path.join(ctx['BUILD_DIR'],
                                ctx['WEBDIR'],
                                'wp-content',
                                ' WARNING_DO_NOT_EDIT_THIS_DIRECTORY')
    with open(warning_file, 'wt') as fp:
        fp.write("!! WARNING !! DO NOT EDIT FILES IN THIS DIRECTORY!!")
        fp.write("\n")
        fp.write("These files are managed by a WordPress instance running "
                 "on CloudFoundry.  Editing them directly may break things "
                 " and changes may be overwritten the next time the "
                 "application is staged on CloudFoundry.")
        fp.write("\n")
        fp.write("YOU HAVE BEEN WARNED!!")


# Extension Methods
def preprocess_commands(ctx):
    return enable_sshfs(ctx)


def service_commands(ctx):
    cmds = {}
    if is_sshfs_enabled(ctx):
        process_ssh_opts(ctx)
        cmds['sshfs'] = ['sshfs', "%s:%s" % (ctx['SSH_HOST'], ctx['SSH_PATH']),
                         '$HOME/%s/wp-content' % ctx['WEBDIR'], '-C', '-f',
                         '-o IdentityFile=$HOME/.ssh/%s' % ctx['SSH_KEY_NAME'],
                         '-o StrictHostKeyChecking=yes',
                         '-o UserKnownHostsFile=$HOME/.ssh/known_hosts',
                         '-o idmap=user']
        cmds['sshfs'].extend(ctx['SSH_OPTS'])
        _log.info("cmd to run `%s`", cmds['sshfs'])

    return cmds


def service_environment(ctx):
    return {}


def compile(install):
    ctx = install.builder._ctx
    merge_defaults(ctx)
    print 'Installing Wordpress %s' % ctx['WORDPRESS_VERSION']
    inst = install._installer
    workDir = os.path.join(ctx['TMPDIR'], 'wordpress')
    inst.install_binary_direct(
        ctx['WORDPRESS_URL'],
        ctx['WORDPRESS_HASH'],
        workDir,
        fileName=ctx['WORDPRESS_PACKAGE'],
        strip=True)
    (install.builder
        .move()
        .everything()
        .under('{BUILD_DIR}/{WEBDIR}')
        .into(workDir)
        .done())
    (install.builder
        .move()
        .everything()
        .under(workDir)
        .into('{BUILD_DIR}/{WEBDIR}')
        .done())
    write_sshfs_warning(ctx)
    return 0
