with open('test_fuwa.py', 'r') as f:
    content = f.read()

content = content.replace('from textual.widgets import Button, Log', 'from textual.widgets import Button, RichLog')
content = content.replace('log_view = app.query_one("#chat_log", Log)', 'log_view = app.query_one("#chat_log", RichLog)')
content = content.replace('assert "Hello World" in log_view.lines[-1]', 'assert "Hello World" in "\\n".join([line.text for line in log_view.lines])')

with open('test_fuwa.py', 'w') as f:
    f.write(content)
