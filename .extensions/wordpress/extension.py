"""WordPress Extension

Downloads, installs and configures WordPress
"""
import os
import os.path
import logging
from build_pack_utils import utils


_log = logging.getLogger('wordpress')


DEFAULTS = utils.FormattedDict({
    'WORDPRESS_VERSION': '3.8.1',  # or 'latest'
    'WORDPRESS_PACKAGE': 'wordpress-{WORDPRESS_VERSION}.tar.gz',
    'WORDPRESS_HASH': '904487e0d70a2d2b6a018aaf99e21608d8f2db88',
    'WORDPRESS_URL': 'https://wordpress.org/{WORDPRESS_PACKAGE}'
})


# Extension Methods
def preprocess_commands(ctx):
    return ()


def service_commands(ctx):
    return {}


def service_environment(ctx):
    return {}


def compile(install):
    print 'Installing Wordpress %s' % DEFAULTS['WORDPRESS_VERSION']
    ctx = install.builder._ctx
    inst = install._installer
    workDir = os.path.join(ctx['TMPDIR'], 'wordpress')
    inst.install_binary_direct(
        DEFAULTS['WORDPRESS_URL'],
        DEFAULTS['WORDPRESS_HASH'],
        workDir,
        fileName=DEFAULTS['WORDPRESS_PACKAGE'],
        strip=True)
    (install.builder
        .move()
        .everything()
        .under('{BUILD_DIR}/htdocs')
        .into(workDir)
        .done())
    (install.builder
        .move()
        .everything()
        .under(workDir)
        .where_name_does_not_match('^%s/setup/.*$' % workDir)
        .into('{BUILD_DIR}/htdocs')
        .done())
    return 0
