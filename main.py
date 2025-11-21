from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.requests import Request
from gender_gusser import apply_gender_guess
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/anaylyze_gender")
async def analyze_gender(req:Request):
    
    body = await req.json()

    usernames_and_full_names = body.get("usernames_and_full_name_list", [])
    male_female_keywords = body.get("male_female_keywords", [])
    
    analyses = [] ## analyses of male and female 

    for username, full_name in usernames_and_full_names:
        
       analyses.append(apply_gender_guess(full_name, username,male_female_keywords))

       
    return {"success":True,"analyses":analyses}

    

    