try:
    import ujson as json
except ImportError:
    try:
        import simplejson as json
    except ImportError:
        try:
            import json
        except ImportError:
            raise ImportError('A json library is required to use this python library')
