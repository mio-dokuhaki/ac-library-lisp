import importlib.machinery
import importlib.util
import os
import sys


def load_existing_sitecustomize():
    own_directory = os.path.realpath(os.path.dirname(__file__))
    paths = [path for path in sys.path if os.path.realpath(path or os.curdir) != own_directory]
    spec = importlib.machinery.PathFinder.find_spec('sitecustomize', paths)
    if spec is None or spec.loader is None:
        return
    current = sys.modules['sitecustomize']
    module = importlib.util.module_from_spec(spec)
    try:
        sys.modules['sitecustomize'] = module
        spec.loader.exec_module(module)
    except Exception as exc:
        print(f'Error in existing sitecustomize: {type(exc).__name__}', file=sys.stderr)
        sys.modules['sitecustomize'] = current


load_existing_sitecustomize()

import decimal
import re
import types


def apply_compatibility():
    try:
        from onlinejudge.service.atcoder import AtCoderProblemData
    except ImportError:
        return

    original = getattr(getattr(AtCoderProblemData, '_from_html', None), '__func__', None)
    code = getattr(original, '__code__', None)
    legacy_pattern = r'^(メモリ制限|Memory Limit): ([0-9.]+) (KB|MB)'
    if code is None or legacy_pattern not in code.co_consts:
        return

    pattern = re.compile(r'^(メモリ制限|Memory Limit): ([0-9]+(?:\.[0-9]+)?) (KiB|MiB)(?=$|[^A-Za-z])')

    def parse(cls, html, **kwargs):
        class RegexProxy:
            match = None

            def __getattr__(self, name):
                return getattr(re, name)

            def search(self, expression, value, *args, **options):
                if expression == legacy_pattern and isinstance(value, str):
                    match = pattern.search(value)
                    if match:
                        self.match = match
                        unit = 'KB' if match.group(3) == 'KiB' else 'MB'
                        value = value[:match.start(3)] + unit + value[match.end(3):]
                return re.search(expression, value, *args, **options)

        proxy = RegexProxy()
        namespace = dict(original.__globals__)
        namespace['re'] = proxy
        parser = types.FunctionType(original.__code__, namespace, original.__name__,
                                    original.__defaults__, original.__closure__)
        parser.__kwdefaults__ = original.__kwdefaults__
        result = parser(cls, html, **kwargs)
        if proxy.match:
            factor = 1024 if proxy.match.group(3) == 'KiB' else 1024 * 1024
            result.memory_limit_byte = int(decimal.Decimal(proxy.match.group(2)) * factor)
        return result

    AtCoderProblemData._from_html = classmethod(parse)


apply_compatibility()
