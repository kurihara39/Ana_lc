import os,glob

today = os.environ["today"]
path = f"/data01/kurihara/Ana_lc/{today}"

files = glob.glob(f"{path}/*.html")

if os.path.exists(f"{path}/{today}")==False:
    os.makedirs(f"{path}/{today}")
    print(f"{path}/{today} is created.")   

with open(f"{path}/README.txt", "w") as f:
    print("## github home", file=f)
    print("https://github.com/kurihara39/Ana_lc", file=f)
    print("", file=f)

    print("## confluence", file=f)
    print("https://e-lab.atlassian.net/wiki/spaces/ELAB/pages/129139550/MAXI", file=f)
    print("", file=f)

    print("## links", file=f)

    for i in files:
        print(i.replace("/data01/kurihara", "https://kurihara39.github.io"), file=f)
    
    print(f"Finished writing on {path}/README.txt")