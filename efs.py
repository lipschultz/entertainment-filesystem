#!/usr/bin/env python3

import os
import sys
from pathlib import Path

from fuse import FUSE
from guessit import guessit

from passthrough import Passthrough


class ESCFS(Passthrough):
    @classmethod
    def real_to_friendly_name(cls, path):
        guessed_info = guessit(path)
        if ('mimetype' not in guessed_info and 'container' not in guessed_info) or len(guessed_info) <= 3:
            return path
        
        if guessed_info['type'] == 'episode':
            return f'S{guessed_info["season"]:02d}E{guessed_info["episode"]:02d} - {guessed_info["episode_title"]}{Path(path).suffix}'
        elif guessed_info['type'] == 'movie':
            year_part = '' if 'year' not in guessed_info else f' ({guessed_info["year"]})'
            alternative_title = '' if 'alternative_title' not in guessed_info else f' - {guessed_info["alternative_title"]}'
            return f'{guessed_info["title"]}{alternative_title}{year_part}{Path(path).suffix}'
        
        return path
    
    @classmethod
    def friendly_to_real_name(cls, path):
        guessed_info = guessit(path)
        if ('mimetype' not in guessed_info and 'container' not in guessed_info) or len(guessed_info) <= 3:
            return path
        
        filepath = Path(path)
        if filepath.exists():
            return path
        
        if guessed_info['type'] == 'episode':
            search_info = {k: guessed_info.get(k) for k in ('type', 'season', 'episode', 'episode_title', 'container', 'mimetype')}
        elif guessed_info['type'] == 'movie':
            search_info = {k: guessed_info.get(k) for k in ('type', 'title', 'alternative_title', 'year', 'container', 'mimetype')}
        else:
            return path
        
        for potential_real_filepath in filepath.parent.glob(f'*{filepath.suffix}'):
            potential_info = guessit(potential_real_filepath)
            if all(search_info[k] == potential_info.get(k) for k in search_info):
                return str(potential_real_filepath)
        return path

    def readdir(self, path, fh):
        full_path = self._full_path(path)

        dirents = ['.', '..']
        if os.path.isdir(full_path):
            dirents.extend(
                self.real_to_friendly_name(p) for p in os.listdir(full_path)
            )
        for r in dirents:
            yield r
        
    def _full_path(self, partial):
        full_path = super()._full_path(partial)
        real_full_path = self.friendly_to_real_name(full_path)
        return real_full_path


def main(mountpoint, root, foreground=True):
    FUSE(ESCFS(root), mountpoint, nothreads=True, foreground=foreground)  # , allow_other=True)


if __name__ == '__main__':
    main(sys.argv[2], sys.argv[1])
