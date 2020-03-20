import pandas as pd
import matplotlib.pyplot as plt

field = 'Homework 2 (203672)'
df = pd.read_csv('hw02_grades.csv')
print(df[field].describe())

print('Failed')
print(df[df[field] < 40][['ID', 'Student']])

df.hist(field)
plt.savefig('mark_hist.png')
