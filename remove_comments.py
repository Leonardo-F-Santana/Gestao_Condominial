import os
import re
import io
import tokenize

def remove_python_comments(source):

    io_obj = io.StringIO(source)
    out = ""
    last_lineno = -1
    last_col = 0

    try:
        for tok in tokenize.generate_tokens(io_obj.readline):
            token_type = tok[0]
            token_string = tok[1]
            start_line, start_col = tok[2]
            end_line, end_col = tok[3]

            if start_line > last_lineno:
                last_col = 0
            if start_col > last_col:
                out += (" " * (start_col - last_col))

            if token_type == tokenize.COMMENT:
                pass
            elif token_type == tokenize.STRING:
                if token_string.startswith(('"""', "'''", 'r"""', "r'''", 'R"""', "R'''", 'u"""', "u'''", 'U"""', "U'''", 'f"""', "f'''", 'F"""', "F'''")):

                    out += token_string
                else:
                    out += token_string
            else:
                out += token_string

            last_lineno = end_line
            last_col = end_col

    except tokenize.TokenError:
        return source
    except Exception:
        return source

    out = re.sub(r'(?m)^\s*(["\']{3}).*?\1\s*$', '', out, flags=re.DOTALL)

    out = re.sub(r'\n\s*\n', '\n\n', out)
    return out

def remove_html_comments(source):

    out = re.sub(r'<!--(.*?)-->', '', source, flags=re.DOTALL)

    out = re.sub(r'{#.*?#}', '', out, flags=re.DOTALL)
    return out

def remove_js_css_comments(source):

    out = re.sub(r'/\*.*?\*/', '', source, flags=re.DOTALL)

    out = re.sub(r'(?<!:)(?<!\w)//.*', '', out)
    return out

def clean_file(filepath):
    ext = os.path.splitext(filepath)[1].lower()

    with open(filepath, 'r', encoding='utf-8') as f:
        try:
            content = f.read()
        except UnicodeDecodeError:

            return False

    orig_content = content

    if ext == '.py':
        content = remove_python_comments(content)
    elif ext == '.html':
        content = remove_html_comments(content)
    elif ext in ['.js', '.css']:
        content = remove_js_css_comments(content)

    if content != orig_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

def main():
    root = r"C:\Users\disci\Desktop\gestao_condominio"
    exclude_dirs = {'venv', 'env', '.venv', '.git', '.vscode', '__pycache__', 'Lib', 'Scripts', 'site-packages', 'Include'}

    changed = 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in exclude_dirs]
        for filename in filenames:
            ext = os.path.splitext(filename)[1].lower()
            if ext in ['.py', '.html', '.css', '.js']:
                filepath = os.path.join(dirpath, filename)
                if clean_file(filepath):
                    changed += 1

    print(f"Cleaned {changed} files.")

if __name__ == '__main__':
    main()
