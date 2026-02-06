from xbbg import blp

# Simple test
try:
    test = blp.bdp('TY1 Comdty', 'PX_LAST')
    print("Bloomberg connection successful!")
    print(test)
except Exception as e:
    print(f"Connection failed: {e}")