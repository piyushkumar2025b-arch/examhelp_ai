import sys, os
sys.path.append(os.getcwd())
from utils.ai_engine import generate
try:
    res = generate('hello, list one fruit')
    print('SUCCESS:', res)
except Exception as e:
    print('ERROR:', e)
