# -*- coding: utf-8 -*-

import fnmatch
from os.path import basename
from abc import ABCMeta, abstractmethod

try:
    from pathspec import PathSpec
    have_pathspec = True
except ImportError:
    have_pathspec = False

DEFAULT_MATCHING_PATTERN = 'fnmatch'

def get_filename_matcher(env, matching_pattern):
    """Get filename matcher for matching_pattern."""

    if matching_pattern in ['fnmatch', '', None]:
        return FnmatchMatcher()
    elif matching_pattern == 'gitignore':
        if have_pathspec:
            return GitIgnoreMatcher()
        else:
            env.log.warn('You should install pathspec for using gitignore matching_pattern')
            return FnmatchMatcher()
    else:
        env.log.warn('Unknown matching_pattern %s', matching_pattern)
        return FnmatchMatcher()



class Matcher(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def match_files(self, filename_patterns, files):
        pass


class FnmatchMatcher(Matcher):
    def match_files(self, filename_patterns, files):
        for fname in files:
            for pattern in filename_patterns:
                if fnmatch.fnmatch(basename(fname), pattern):
                    yield fname


class GitIgnoreMatcher(Matcher):
    def match_files(self, filename_patterns, files):
        spec = PathSpec.from_lines('gitignore', filename_patterns)
        return spec.match_files(files)
