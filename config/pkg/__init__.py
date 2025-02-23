################################################################################
#                                                                              #
#         This file is part of the C! library.  A.K.A the cbang library.       #
#                                                                              #
#               Copyright (c) 2021-2025, Cauldron Development  Oy              #
#               Copyright (c) 2003-2021, Cauldron Development LLC              #
#                              All rights reserved.                            #
#                                                                              #
#        The C! library is free software: you can redistribute it and/or       #
#       modify it under the terms of the GNU Lesser General Public License     #
#      as published by the Free Software Foundation, either version 2.1 of     #
#              the License, or (at your option) any later version.             #
#                                                                              #
#       The C! library is distributed in the hope that it will be useful,      #
#         but WITHOUT ANY WARRANTY; without even the implied warranty of       #
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU      #
#                Lesser General Public License for more details.               #
#                                                                              #
#        You should have received a copy of the GNU Lesser General Public      #
#                License along with the C! library.  If not, see               #
#                        <http://www.gnu.org/licenses/>.                       #
#                                                                              #
#       In addition, BSD licensing may be granted on a case by case basis      #
#       by written permission from at least one of the copyright holders.      #
#          You may request written permission by emailing the authors.         #
#                                                                              #
#                 For information regarding this software email:               #
#                                Joseph Coffland                               #
#                         joseph@cauldrondevelopment.com                       #
#                                                                              #
################################################################################

'''Builds an OSX single component flat dist package'''

import os
import shutil
import glob

from SCons.Script import *

deps = ['codesign', 'notarize']


# https://stackoverflow.com/a/65450788
# fast xml escape
xml_escape_table = str.maketrans({
    "<": "&lt;",
    ">": "&gt;",
    "&": "&amp;",
    "'": "&apos;",
    '"': "&quot;",
})
def xml_escape(txt):
    return txt.translate(xml_escape_table)


def InstallApps(env, key, target):
    # copy apps, preserving symlinks, no ignores
    for src in env.get(key):
        if isinstance(src, (list, tuple)) and len(src) in (2, 3):
            src_path = src[0]
            dst_path = os.path.join(target, src[1])
        else:
            src_path = src
            dst_path = os.path.join(target, os.path.basename(src))

        shutil.copytree(src_path, dst_path, True)


def build_function(target, source, env):
    # delete old package build dir
    build_dir = 'build/pkg'
    if os.path.exists(build_dir): shutil.rmtree(build_dir)

    # pkg_id
    if env.get('app_id') and not env.get('pkg_id'):
        env.Replace(pkg_id = env.get('app_id') + '.pkg')
    if not env.get('pkg_id'):
        raise Exception('neither pkg_id nor app_id is set')

    version = env.get('version')
    if not version: raise Exception('version is not set')

    # Make root dir
    root_dir = os.path.join(build_dir, 'root')
    os.makedirs(root_dir, 0o755)

    build_dir_packages = os.path.join(build_dir, 'Packages')
    os.makedirs(build_dir_packages, 0o755)

    build_dir_resources = os.path.join(build_dir, 'Resources')
    os.makedirs(build_dir_resources, 0o755)

    # Apps
    if env.get('pkg_apps'):
        d = os.path.join(root_dir, 'Applications')
        os.makedirs(d, 0o755)
        InstallApps(env, 'pkg_apps', d)

    # Other files
    if env.get('pkg_files'):
        env.InstallFiles('pkg_files', root_dir)

    pkg_resources = env.get('pkg_resources')
    if pkg_resources:
        if not isinstance(pkg_resources, (list, tuple)):
            pkg_resources = [[pkg_resources, '.']]
        env.CopyToPackage(pkg_resources, build_dir_resources)

    for pattern in env.get('sign_apps', []):
        for path in glob.glob(os.path.join(root_dir, pattern)):
            env.SignApplication(path)

    for pattern in env.get('sign_tools', []):
        for path in glob.glob(os.path.join(root_dir, pattern)):
            env.SignExecutable(path)

    # build component pkg
    cmd = ['${PKGBUILD}',
           '--root', root_dir,
           '--id', env.get('pkg_id'),
           '--version', version,
           '--install-location', env.get('pkg_install_to', '/'),
           ]
    if env.get('pkg_scripts'): cmd += ['--scripts', env.get('pkg_scripts')]
    if env.get('pkg_plist'): cmd += ['--component-plist', env.get('pkg_plist')]
    component_pkg = build_dir_packages + '/%s.pkg' % env.get('package_name')
    cmd += [component_pkg]

    env.RunCommandOrRaise(cmd)

    # Filter distribution.xml
    dist = None
    if env.get('pkg_distribution'):
        with open(env.get('pkg_distribution'), 'r') as f: data = f.read()
        dist = build_dir + '/distribution.xml'
        # make xml escaped str values dict for distribution.xml insertion
        xenv = {}
        for key in env.keys():
            value = env[key]
            if isinstance(value, (str, bytes)):
                xenv[key] = xml_escape(str(value))
        with open(dist, 'w') as f: f.write(data % xenv)
    # TODO else build distribution.xml similar to flatdistpkg

    # productbuild command
    cmd = ['${PRODUCTBUILD}', '--version', version]
    if dist:
        cmd += ['--distribution', dist]
        cmd += ['--package-path', build_dir_packages]
    elif component_pkg:
        print("WARNING: No distribution specified. Using --package.")
        cmd += ['--package', component_pkg]
    else:
        print("WARNING: No distribution specified. Using --root.")
        cmd += ['--root', root_dir, env.get('pkg_install_to', '/'),
                '--id', env.get('pkg_id')]
        scripts = env.get('pkg_scripts')
        if scripts: cmd += ['--scripts', scripts]

    cmd += ['--resources', build_dir_resources]

    if env.get('sign_id_installer') and not env.get('sign_disable'):
        cmd += ['--sign', env.get('sign_id_installer'), '--timestamp']
        if env.get('sign_keychain'):
            cmd += ['--keychain', env.get('sign_keychain')]

    cmd += [str(target[0])]

    env.RunCommandOrRaise(cmd)
    env.NotarizeWaitStaple(str(target[0]), timeout = 1200)


def generate(env):
    env.SetDefault(PKGBUILD = 'pkgbuild')
    env.SetDefault(PRODUCTBUILD = 'productbuild')

    bld = Builder(action = build_function,
                  source_factory = SCons.Node.FS.Entry,
                  source_scanner = SCons.Defaults.DirScanner)
    env.Append(BUILDERS = {'Pkg' : bld})

    for tool in deps: env.CBLoadTool(tool)

    return True


def exists():
    return 1
