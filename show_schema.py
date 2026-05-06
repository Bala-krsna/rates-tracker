import sqlite3

conn = sqlite3.connect("data/rates.db")
cur = conn.cursor()

output = []
for row in cur.execute("SELECT name, sql FROM sqlite_master WHERE type='table'"):
    output.append(f"--- {row[0]} ---")
    output.append(row[1])
    output.append("")

text = "\n".join(output)
print(text)

with open("schema_output.txt", "w") as f:
    f.write(text)

conn.close()
print("\n(Also saved to schema_output.txt)")