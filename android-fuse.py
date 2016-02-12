import re
import subprocess
import logging
from fuse import FUSE, FuseOSError, Operations, LoggingMixIn
import errno
import time
import stat

TMP_FILE_NAME = 'tmpfile.tmp'

def build_mode(etype, uperm, gperm, operm):
    mode = {'d': stat.S_IFDIR, 'l': stat.S_IFLNK, '-': stat.S_IFREG}[etype]
    def set_perms(p, r, w, x):
        mode = 0
        if p[0] == 'r':
            mode |= r
        if p[1] == 'w':
            mode |= w
        if p[2] == 'x':
            mode |= x
        return mode
    mode |= set_perms(uperm, stat.S_IRUSR, stat.S_IWUSR, stat.S_IXUSR)
    mode |= set_perms(gperm, stat.S_IRGRP, stat.S_IWGRP, stat.S_IXGRP)
    mode |= set_perms(operm, stat.S_IROTH, stat.S_IWOTH, stat.S_IXOTH)

    return mode

ls_pat = r'^([dl-])([-rwx]{3})([-rwx]{3})([-rwx]{3})\s+(\w+)\s+(\w+)\s+(\d*)\s+([-0-9]{10} \d\d:\d\d)\s(.+)$'

def gen_ino(pathname):
    import hashlib
    m = hashlib.md5()
    m.update(pathname)
    return int(m.hexdigest()[:8], 16)

def parse_ls_line(line):
    m =  re.match(ls_pat, line)
    if m is None:
        print("Could not parse [{}]".format(line))
        return {}
    etype, uperm, gperm, operm, owner, gowner, size, mtime, pathname = m.groups()
    if "->" in pathname:
        pathname, ltarget = pathname.split('->')
        pathname = pathname.strip()
        ltarget  = ltarget.strip()
    else:
        ltarget = None
    size =(int(size) if size else 0)
    return {
            'etype': etype,
            'st_mode': build_mode(etype, uperm, gperm, operm),
            'st_uid': int(owner),
            'st_gid': int(gowner),
            'st_mtime': time.mktime(time.strptime(mtime, '%Y-%m-%d %H:%M')),
            'st_size': size,
            'st_blksize': 8192,
            'st_blocks': size//512 + bool(size % 512),
            'pathname': pathname,
            'ltarget': ltarget,

            # Now, we make up data:
            'st_nlink': 1,
            'st_ino': gen_ino(pathname),
            }


def lsdir(path):
    p = subprocess.Popen(["adb", "shell", "ls", "-nl", "'{}'".format(path)], stdout=subprocess.PIPE)
    data = p.stdout.read()
    for line in data.splitlines():
        yield parse_ls_line(line)

class AndroidADBFuse(LoggingMixIn, Operations):
    def __init__(self):
        self.tmpfile = None
        self.data = None
        pass

    def readdir(self, pathname, fh):
        return ['.', '..'] + [entry['pathname'] for entry in lsdir(pathname)]

    def getattr(self, path, fh=None):
        p = subprocess.Popen(["adb", "shell", "ls", "-lnd", "'{}'".format(path)], stdout=subprocess.PIPE)
        data = p.stdout.read()
        if data == "{}: No such file or directory\r\n".format(path):
            raise FuseOSError(errno.ENOENT)
        for line in data.splitlines():
            r = parse_ls_line(data)
            if len(r) == 0:
                print("COULD NOT getattr for [{}]".format(line))
                raise FuseOSError(errno.ENOENT)
            return r

    def read(self, pathname, size, offset, fh):
        if self.tmpfile != pathname:
            import os
            p = subprocess.call(["adb", "pull", pathname, TMP_FILE_NAME])
            if p != 0:
                raise FuseOSError(errno.EIO)
            self.tmpfile = pathname
            self.data = open(TMP_FILE_NAME, "rb").read()
            os.unlink(TMP_FILE_NAME)
        if offset > len(self.data):
            return 0
        return self.data[offset:offset+size]

    def readlink(self, path):
        attrs = self.getattr(path)
        return attrs['ltarget']

    def rmdir(self, pathname):
        p = subprocess.call(["adb", "shell", "rmdir", "'{}'".format(pathname),])
        if p != 0:
            raise FuseOSError(errno.EIO)

    def unlink(self, pathname):
        p = subprocess.call(["adb", "shell", "rm", "'{}'".format(pathname),])
        if p != 0:
            raise FuseOSError(errno.EIO)


def main(argv):
    if len(argv) != 2:
        print('usage: {} <mountpoint>'.format(argv[0]))
        from sys import exit
        exit(1)

    logging.getLogger('fuse.log-mixin').setLevel(logging.DEBUG)
    f = FUSE(AndroidADBFuse(), argv[1], foreground=True)

if __name__ == '__main__':
    print("THIS IS COMPLETELY EXPERIMENTAL SOFTWARE")
    print("IT MAY DELETE DATA, CALL VALUE-ADDED LINES, OR ANYTHING ELSE")
    print("USE AT YOUR OWN RISK\n")
    import sys
    main(sys.argv)
