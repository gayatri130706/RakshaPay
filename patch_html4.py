import re

with open('static/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Remove the default values so it's clearly an empty input form for any user
html = html.replace('id=\"input-sender-name\" value=\"Gayatri\"', 'id=\"input-sender-name\" value=\"\"')
html = html.replace('id=\"input-sender-vpa\" value=\"gayatri@okaxis\"', 'id=\"input-sender-vpa\" value=\"\"')

with open('static/index.html', 'w', encoding='utf-8') as f:
    f.write(html)
