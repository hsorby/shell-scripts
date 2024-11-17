with open('tests/issueTracking.txt') as f:
  content = f.readlines()

r = []
for c in content:
  c = c.strip()
  if c and c not in r:
    r.append(c)


for i in r:
  print(i)

