from typing import Any, List

def fmt(header: List[str], rows: List[List[any]], separators=False, str_converter=None) -> str:
    # go through each column and find what the longest one is
    str_converter = str_converter if str_converter else str
    max_lengths = [len(h) for h in header]
    rows_copy = [list(r) for r in rows]

    for r in range(len(rows)):
        for c in range(len(rows[r])):
            rows_copy[r][c] = str_converter(rows[r][c])
            max_lengths[c] = max(max_lengths[c], len(rows[r][c]))
    
    header_str = ' ┃ '.join(f'%{max_lengths[i]}s' % header[i] for i in range(len(max_lengths)))
    line_separators = ''
    for i in range(len(max_lengths)):
        # first col doesn't need extra '-'
        line_separators += '-'*(max_lengths[i]+2 - (i==0))
        if i < len(max_lengths)-1:
            line_separators += '╋'
        else:
            line_separators += '━'   

    body = ''
    for r in rows_copy:
        body += ' | '.join(f'%{max_lengths[i]}s' % r[i] for i in range(len(max_lengths))) + '\n'
        if separators:
            body += line_separators + '\n'

    content = header_str + '\n' + line_separators + '\n' + body
    if not separators:
        content += line_separators

    return content