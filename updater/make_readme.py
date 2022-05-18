import os,glob

today = os.environ["today"]
path = f"/data01/kurihara/Ana_lc/{today}"

files = glob.glob(f"{path}/*.html")

with open(f"{path}/README.txt", "a") as f:
    print("## github home", file=f)
    print("https://github.com/kurihara39/Ana_lc", file=f)
    print("", file=f)
    print("## links", file=f)

    for i in files:
        print(i.replace("/data01/kurihara", "https://kurihara39.github.io"), file=f)
    
    print(f"Finished writing on {path}/README.txt")