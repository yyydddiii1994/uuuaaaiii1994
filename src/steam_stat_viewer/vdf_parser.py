import re

def parse_vdf(content):
    """
    Parses a VDF (Valve Data Format) string into a Python dictionary.
    This is a simplified parser and might not handle all edge cases,
    but should work for typical config files.
    """
    # Remove comments
    content = re.sub(r'//.*', '', content)

    # Tokenize: quoted strings or structural braces
    # This regex matches: "quoted string" OR { OR }
    tokens = re.findall(r'"((?:[^"\\]|\\.)*)"|({)|(})', content)

    stack = [{}]
    expect_key = True
    current_key = None

    for match in tokens:
        string_val, brace_open, brace_close = match

        if brace_open:
            if current_key is None:
                # Should not happen in valid VDF where { follows a key
                continue
            new_dict = {}
            stack[-1][current_key] = new_dict
            stack.append(new_dict)
            expect_key = True
            current_key = None

        elif brace_close:
            if len(stack) > 1:
                stack.pop()
            expect_key = True

        elif string_val is not None:
            # Unescape string
            val = string_val.encode('utf-8').decode('unicode_escape')

            if expect_key:
                current_key = val
                expect_key = False
            else:
                # It's a value
                stack[-1][current_key] = val
                current_key = None
                expect_key = True

    return stack[0]

def parse_acf(content):
    """
    Parses ACF files (AppManifest), which are similar to VDF but usually simpler.
    Reuses the VDF parser.
    """
    return parse_vdf(content)
